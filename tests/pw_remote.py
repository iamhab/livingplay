import sys, json, time, re
from playwright.sync_api import sync_playwright
url, out = sys.argv[1], sys.argv[2]
res = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("light", "dark"):
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, color_scheme=scheme, has_touch=True, is_mobile=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(url); pg.wait_for_selector("#q div", timeout=8000); time.sleep(.5)
        res[scheme + "_title"] = pg.inner_text("#title")
        res[scheme + "_dev"] = pg.inner_text("#dev")
        res[scheme + "_sub"] = pg.inner_text("#sub")
        res[scheme + "_q"] = pg.locator("#q div").count()
        res[scheme + "_hscroll"] = pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth")
        res[scheme + "_minbtn"] = pg.evaluate("Math.min(...[...document.querySelectorAll('button')].map(b=>b.getBoundingClientRect().height))")
        res[scheme + "_errs"] = errs[:3]
        pg.screenshot(path=f"{out}_{scheme}.png", full_page=True)
        if scheme == "light":
            pg.click("#pp"); time.sleep(1.0)
            res["after_click_pp"] = pg.evaluate("document.getElementById('pp').innerHTML.includes('M6 5h4')")
            pg.click("#tgp"); time.sleep(1.5)
            res["target_after_click"] = pg.evaluate("document.getElementById('tgp').className")
            pg.click("#tgc"); time.sleep(1.5)
            pg.locator("#q div").nth(1).click(); time.sleep(1.0)
        ctx.close()
    # servidor fora do ar -> aviso
    ctx = b.new_context(viewport={"width": 390, "height": 844}); pg = ctx.new_page(); pg.goto(url); pg.wait_for_selector("#q div")
    pg.route(re.compile(r"/api/state"), lambda r: r.abort()); pg.wait_for_timeout(9000)
    res["offline_banner"] = pg.is_visible("#net")
    b.close()
print(json.dumps(res, ensure_ascii=False))
