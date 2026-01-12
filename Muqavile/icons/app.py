import streamlit as st
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import io
import os
import re

# ---------------------------------------------------------
# 1. TƏNZİMLƏMƏLƏR
# ---------------------------------------------------------
WHITE = (255, 255, 255)
GRAY_TEXT = (200, 200, 200)

# Şrift və Dizayn tənzimləmələri
VERTICAL_OFFSET = 40 
ICON_X = 50
TEXT_X = 110
START_Y = 340 + VERTICAL_OFFSET 
ROW_GAP = 100
ICON_SIZE = 45

# Qiymət Xanalarının Yeri
FIXED_PRICE_Y = 1055
PRICE1_CENTER_X = 275 
PRICE2_CENTER_X = 515

# A4 Vərəq Ölçüləri (300 DPI)
A4_W, A4_H = 2480, 3508

# ---------------------------------------------------------
# 2. KÖMƏKÇİ FUNKSİYALAR
# ---------------------------------------------------------
def load_font(name, size):
    try:
        path = os.path.join("fonts", name)
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def make_white(image):
    image = image.convert("RGBA")
    white_img = Image.new("RGBA", image.size, (255, 255, 255, 255))
    final_img = Image.composite(white_img, Image.new("RGBA", image.size, (0,0,0,0)), image)
    return final_img

def clean_price_text(text):
    if not text: return ""
    return re.sub(r'[^\d]', '', text)

def scrape_smart(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    data = {
        "Brand": "", "Model": "", "PartNumber": "", 
        "CPU": "", "RAM": "", "SSD": "", "GPU": "", 
        "Screen": "", "OS": "Windows 11", 
        "PriceOld": "", "PriceNew": ""
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator="\n")

        # 1. Başlıq
        title_tag = soup.find("h1")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            parts = title_text.split(" ", 2)
            if len(parts) > 0: data["Brand"] = parts[0].strip()
            if len(parts) > 1: data["Model"] = parts[1].strip()
            if len(parts) > 2: data["PartNumber"] = parts[2].strip()

        # 2. Qiymətlər
        price_old_tag = soup.find(class_="price-old")
        if price_old_tag:
            data["PriceOld"] = clean_price_text(price_old_tag.get_text())
            
        price_new_tag = soup.find(class_="price-new")
        if price_new_tag:
            data["PriceNew"] = clean_price_text(price_new_tag.get_text())
        else:
            price_normal_tag = soup.find(class_="product-price")
            if price_normal_tag:
                data["PriceNew"] = clean_price_text(price_normal_tag.get_text())

        # 3. Parametrlər
        regexes = {
            "CPU": r'(?:CPU|Prosessor)\s*:\s*([^\n\r]+)',
            "RAM": r'(?:RAM|Operativ)\s*:\s*([^\n\r]+)',
            "SSD": r'(?:SSD|Yaddaş)\s*:\s*([^\n\r]+)',
            "Screen": r'(?:Ekran|Display)\s*:\s*([^\n\r]+)',
            "GPU": r'(?:VGA|GPU|Video|Qrafik)\s*:\s*([^\n\r]+)',
            "OS": r'(?:OS|Əməliyyat sistemi)\s*:\s*([^\n\r]+)'
        }

        for key, pattern in regexes.items():
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                val = m.group(1).strip()
                clean_val = re.sub(r'[^\w\s\-\.\,\(\)\"\/]', '', val)
                data[key] = clean_val[:65] 

        return data, None

    except Exception as e:
        return data, str(e)

# ---------------------------------------------------------
# 3. DİZAYN FUNKSİYASI (LOGO SİLİNDİ)
# ---------------------------------------------------------
def create_final_design(data, price1, price2, credit):
    try:
        base_img = Image.open("template.png").convert("RGB")
    except:
        return None

    W, H = base_img.size 
    img = Image.new('RGB', (W, H), color=(54, 54, 64))
    img.paste(base_img, (0, 0))
    draw = ImageDraw.Draw(img)

    # Fontlar
    font_brand = load_font("TitilliumWeb-Bold.ttf", 60)
    font_model = load_font("TitilliumWeb-Bold.ttf", 55)
    font_pn    = load_font("TitilliumWeb-Bold.ttf", 34)
    font_spec  = load_font("TitilliumWeb-Bold.ttf", 38)
    font_price_main = load_font("TitilliumWeb-Bold.ttf", 68)
    
    # Mətnlər
    if data["Brand"]:
        w = draw.textlength(data["Brand"], font=font_brand)
        draw.text(((W - w) / 2, 40 + VERTICAL_OFFSET), data["Brand"], font=font_brand, fill=WHITE)
    
    if data["Model"]:
        w = draw.textlength(data["Model"], font=font_model)
        draw.text(((W - w) / 2, 110 + VERTICAL_OFFSET), data["Model"], font=font_model, fill=WHITE)
    
    if data["PartNumber"]:
        w = draw.textlength(data["PartNumber"], font=font_pn)
        draw.text(((W - w) / 2, 220 + VERTICAL_OFFSET), data["PartNumber"], font=font_pn, fill=GRAY_TEXT)

    specs = [
        ("cpu", data["CPU"]), ("ram", data["RAM"]), ("ssd", data["SSD"]),
        ("gpu", data["GPU"]), ("screen", data["Screen"]), ("os", data["OS"]),
    ]

    y = START_Y
    for icon_name, text in specs:
        icon_path = os.path.join("icons", f"{icon_name}.png")
        if os.path.exists(icon_path):
            try:
                icon = Image.open(icon_path).convert("RGBA")
                icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
                icon = make_white(icon) 
                img.paste(icon, (ICON_X, y), icon)
            except: pass
        
        if text:
            max_w = W - TEXT_X - 20
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if draw.textlength(test_line, font=font_spec) < max_w:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)

            for i, line in enumerate(lines):
                draw.text((TEXT_X, y + (i * 42) - 5), line, font=font_spec, fill=WHITE)
        y += ROW_GAP + 10

    # Qiymətlər
    if price1:
        draw.text((PRICE1_CENTER_X, FIXED_PRICE_Y), str(price1), font=font_price_main, fill=WHITE, anchor="mm")
    if price2:
        draw.text((PRICE2_CENTER_X, FIXED_PRICE_Y), str(price2), font=font_price_main, fill=WHITE, anchor="mm")
    if credit:
        draw.text((W/2, 1130), f"Kredit: {credit}", font=font_spec, fill=WHITE, anchor="mm")

    return img

# ---------------------------------------------------------
# 4. A4 YARATMA FUNKSİYASI
# ---------------------------------------------------------
def create_a4_sheet(images_list):
    a4_img = Image.new('RGB', (A4_W, A4_H), color=(255, 255, 255))
    gap_x = (A4_W - (800 * 2)) // 3
    gap_y = (A4_H - (1150 * 2)) // 3
    
    positions = [
        (gap_x, gap_y),                         
        (gap_x + 800 + gap_x, gap_y),           
        (gap_x, gap_y + 1150 + gap_y),          
        (gap_x + 800 + gap_x, gap_y + 1150 + gap_y) 
    ]

    for i, img_bytes in enumerate(images_list):
        if i >= 4: break 
        try:
            card = Image.open(io.BytesIO(img_bytes))
            a4_img.paste(card, positions[i])
        except: pass
        
    return a4_img

# ---------------------------------------------------------
# 5. STREAMLIT UI
# ---------------------------------------------------------
st.set_page_config(page_title="LaptopMarket", layout="centered")

c_logo, c_title = st.columns([1, 4]) 
with c_logo:
    logo_path_ui = os.path.join("icons", "logo.png")
    if os.path.exists(logo_path_ui):
        st.image(logo_path_ui, width=130)

with c_title:
    st.title("LaptopMarket qiymət etiketi hazırla")

if "specs" not in st.session_state:
    st.session_state.specs = {
        "Brand": "", "Model": "", "PartNumber": "", 
        "CPU": "", "RAM": "", "SSD": "", "GPU": "", 
        "Screen": "", "OS": "Windows 11", 
        "PriceOld": "", "PriceNew": "" 
    }
if "generated_image" not in st.session_state:
    st.session_state.generated_image = None
if "print_queue" not in st.session_state:
    st.session_state.print_queue = []

# Sidebar
st.sidebar.header(f"🗂️ Siyahı: {len(st.session_state.print_queue)} / 4")
if st.sidebar.button("🗑️ Siyahını Təmizlə"):
    st.session_state.print_queue = []
    st.rerun()

if len(st.session_state.print_queue) > 0:
    st.sidebar.success("Siyahıda şəkillər var!")
    if st.sidebar.button("📄 A4 Vərəqi Yarat"):
        final_a4 = create_a4_sheet(st.session_state.print_queue)
        st.write("## 🎉 Hazır A4 Vərəqi")
        st.image(final_a4, caption="Çap üçün hazırdır", use_container_width=True)
        buf = io.BytesIO()
        final_a4.save(buf, format="PDF") 
        st.download_button("📥 A4 PDF Yüklə", buf.getvalue(), "qiymetler_A4.pdf", "application/pdf")

# Əsas Hissə
col1, col2 = st.columns([3, 1])
url = col1.text_input("Link:")
if col2.button("Parametrləri Gətir"):
    with st.spinner("Gətirilir..."):
        data, err = scrape_smart(url)
        if not err:
            st.session_state.specs = data
            st.success("Tapıldı!")
        else:
            st.error("Tapılmadı, əllə daxil edin.")

st.write("### 1. Etiketi Dizayn Edin")
with st.form("design_form"):
    s = st.session_state.specs
    
    c1, c2, c3 = st.columns([2, 2, 2])
    brand = c1.text_input("Brend", s["Brand"])
    model = c2.text_input("Model", s["Model"])
    pn    = c3.text_input("Part No", s["PartNumber"])
    
    st.markdown("---")
    c4, c5 = st.columns(2)
    cpu = c4.text_input("CPU", s["CPU"])
    ram = c5.text_input("RAM", s["RAM"])
    ssd = c4.text_input("SSD", s["SSD"])
    gpu = c5.text_input("GPU", s["GPU"])
    scr = c4.text_input("Ekran", s["Screen"])
    os_ = c5.text_input("OS", s["OS"])
    
    st.markdown("---")
    st.write("💰 **Qiymət Xanaları**")
    cp1, cp2, cc = st.columns(3)
    
    p1_default = s.get("PriceOld", "")
    p1_val = cp1.text_input("Sol Xana (Köhnə)", value=p1_default)
    
    p2_default = s.get("PriceNew", "")
    p2_val = cp2.text_input("Orta Xana (Yeni)", value=p2_default)
    
    cred_val = cc.text_input("Kredit", placeholder="65 AZN/ay")
    
    submitted = st.form_submit_button("🎨 Tək Şəkli Hazırla")
    
    if submitted:
        final_data = {
            "Brand": brand, "Model": model, "PartNumber": pn,
            "CPU": cpu, "RAM": ram, "SSD": ssd, 
            "GPU": gpu, "Screen": scr, "OS": os_
        }
        img = create_final_design(final_data, p1_val, p2_val, cred_val)
        st.session_state.generated_image = img

# Nəticə
if st.session_state.generated_image:
    st.write("---")
    c_img, c_btn = st.columns([2, 1])
    c_img.image(st.session_state.generated_image, caption="Cari Etiket", width=300)
    c_btn.write("### Bəyəndiniz?")
    if c_btn.button("➕ Siyahıya Əlavə Et"):
        buf = io.BytesIO()
        st.session_state.generated_image.save(buf, format="PNG")
        st.session_state.print_queue.append(buf.getvalue())
        st.success(f"Əlavə olundu! Siyahıda {len(st.session_state.print_queue)} ədəd var.")
        st.rerun()