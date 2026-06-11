from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc") if bold else Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def main() -> None:
    width, height = 1600, 1000
    image = Image.new("RGB", (width, height), "#f6f5ef")
    draw = ImageDraw.Draw(image)

    def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        return load_font(size, bold)

    draw.rectangle([0, 0, width, 185], fill="#173f36")
    draw.text((64, 42), "期末复习教练：像给大学生请了个一对一家教老师", font=font(42, True), fill="white")
    draw.text((66, 108), "真实产出展示：原理动画互动网页 + 毛思主线图 + 费曼式回忆检测", font=font(24), fill="#dceee7")
    draw.rounded_rectangle([1035, 64, 1515, 132], radius=18, fill="#f2b84b")
    draw.text((1060, 82), "把资料喂给 AI，就开始一对一带学", font=font(25, True), fill="#2e2108")

    def card(x: int, y: int, w: int, h: int, title: str, subtitle: str) -> None:
        shadow = Image.new("RGBA", (w + 22, h + 22), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle([11, 11, w + 11, h + 11], radius=24, fill=(31, 41, 51, 34))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        image.paste(shadow, (x - 11, y - 11), shadow)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=22, fill="white", outline="#ddd7ca", width=2)
        draw.text((x + 24, y + 20), title, font=font(28, True), fill="#173f36")
        draw.text((x + 24, y + 58), subtitle, font=font(18), fill="#6b6257")

    card(50, 220, 710, 500, "原理动画：复杂原理先看懂", "少量 token 生成互动网页，拖动参数理解土力学三相指标")
    soil = Image.open(ASSETS / "soil-three-phase-real.png").convert("RGB")
    soil.thumbnail((662, 390))
    image.paste(soil, (74, 310))

    card(800, 220, 750, 500, "文科带学：先建主线图", "毛思课程用总图、主线和主动回忆，不强行动画化")
    mao = Image.open(ASSETS / "mao-mindmap-real.png").convert("RGB")
    mao.thumbnail((700, 390))
    image.paste(mao, (824, 310))

    card(50, 755, 710, 190, "解决的真实痛点", "零碎时间不知道看啥 · 原理文字难懂 · 重点抓不住 · 背诵没人检查 · 答疑没人陪")
    bullets = [
        "喂给 AI：PDF 课本 / 老师 PPT / 笔记 / 往年题",
        "自动拆重点：材料清单 → 提分地图 → 第一学习块",
        "全过程机制：费曼讲解 + 艾宾浩斯间隔复习 + 短测纠错",
    ]
    y = 842
    for bullet in bullets:
        draw.ellipse([76, y + 8, 88, y + 20], fill="#d79b27")
        draw.text((100, y), bullet, font=font(20), fill="#26352f")
        y += 33

    card(800, 755, 750, 190, "真实带学对话摘录", "用户回答后即时检查、纠偏、继续推进下一块")

    def bubble(y_pos: int, speaker: str, text: str, fill: str, outline: str) -> None:
        draw.rounded_rectangle([830, y_pos, 1515, y_pos + 44], radius=14, fill=fill, outline=outline, width=2)
        draw.text((846, y_pos + 9), speaker, font=font(18, True), fill="#173f36")
        draw.text((925, y_pos + 9), text, font=font(18), fill="#26352f")

    bubble(815, "学生", "科学指南，精神财富，第一次历史性飞跃。", "#eef6ff", "#bad2ef")
    bubble(867, "教练", "答对了。继续进入新民主主义革命：总路线、道路、前途。", "#fffaf0", "#efd9a8")
    bubble(919, "学生", "统一战线和武装斗争是基本武器，党的建设是伟大工程。", "#eef6ff", "#bad2ef")

    image.save(ASSETS / "product-showcase-real.png", quality=95)


if __name__ == "__main__":
    main()
