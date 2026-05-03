import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import qrcode
import hashlib
import json
import os
import re
from datetime import datetime
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="URL Shortener",
    page_icon="🔗",
    layout="wide"
)

st.title("🔗 URL Shortener & Link Analytics")
st.markdown("Shorten URLs, generate QR codes "
            "and track link performance.")
st.markdown("---")

# Data persistence
DATA_FILE = "links.json"

def load_links():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_links(links):
    with open(DATA_FILE, 'w') as f:
        json.dump(links, f, indent=2)

def generate_short_code(url):
    hash_val = hashlib.md5(
        (url + str(datetime.now())).encode()
    ).hexdigest()[:6]
    return hash_val.upper()

def is_valid_url(url):
    pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)'
        r'+[A-Z]{2,6}\.?|localhost|\d{1,3}\.\d{1,3}'
        r'\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )
    return bool(pattern.match(url))

def generate_qr(url):
    qr  = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(
        fill_color="black",
        back_color="white"
    )
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

# Load links
links = load_links()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "✂️ Shorten",
    "📊 Analytics",
    "🔍 My Links",
    "📱 QR Generator"
])

# Tab 1 — Shorten
with tab1:
    st.markdown("### Shorten a URL")

    col1, col2 = st.columns([2, 1])

    with col1:
        long_url = st.text_input(
            "Enter your long URL:",
            placeholder="https://example.com/very/long/url"
        )
        custom_code = st.text_input(
            "Custom short code (optional):",
            placeholder="e.g. mylink",
            max_chars=10
        )
        label = st.text_input(
            "Label (optional):",
            placeholder="e.g. My portfolio"
        )

        if st.button("✂️ Shorten URL", type="primary"):
            if not long_url:
                st.warning("Please enter a URL.")
            elif not is_valid_url(long_url):
                st.error("Invalid URL. Include "
                         "http:// or https://")
            else:
                code = custom_code.strip().upper() \
                       if custom_code.strip() \
                       else generate_short_code(long_url)

                if code in links:
                    st.warning(f"Code '{code}' already "
                               f"exists. Try another.")
                else:
                    links[code] = {
                        'original':  long_url,
                        'code':      code,
                        'label':     label or long_url[:40],
                        'created':   datetime.now().strftime(
                            '%Y-%m-%d %H:%M'),
                        'clicks':    0,
                        'click_log': []
                    }
                    save_links(links)

                    short_url = f"rasdel7.short/{code}"
                    st.success("✅ URL shortened!")
                    st.markdown(
                        f"### 🔗 `{short_url}`"
                    )
                    st.code(short_url)

                    col_a, col_b = st.columns(2)
                    col_a.metric("Short Code", code)
                    col_b.metric("Original Length",
                                 f"{len(long_url)} chars")

                    # QR
                    qr_buf = generate_qr(long_url)
                    st.image(qr_buf,
                             caption="QR Code for your URL",
                             width=200)
                    st.download_button(
                        "⬇️ Download QR Code",
                        qr_buf,
                        f"qr_{code}.png",
                        "image/png"
                    )

    with col2:
        st.markdown("### 📌 Quick Stats")
        total_links  = len(links)
        total_clicks = sum(
            v['clicks'] for v in links.values())
        st.metric("Total Links",  total_links)
        st.metric("Total Clicks", total_clicks)

        if links:
            top = max(links.values(),
                      key=lambda x: x['clicks'])
            st.metric("Most Clicked",
                      f"{top['clicks']} clicks")
            st.caption(top['label'][:30])

        st.markdown("### 💡 Tips")
        st.info("""
        - Use custom codes for branded links
        - Add labels to track campaigns
        - Generate QR codes for offline use
        - View analytics in the Analytics tab
        """)

# Tab 2 — Analytics
with tab2:
    st.markdown("### Link Analytics")

    if not links:
        st.info("No links created yet. "
                "Shorten a URL first!")
    else:
        df = pd.DataFrame([{
            'Label':    v['label'][:30],
            'Code':     k,
            'Clicks':   v['clicks'],
            'Created':  v['created'],
            'Original': v['original'][:50] + '...'
                        if len(v['original']) > 50
                        else v['original']
        } for k, v in links.items()])

        # Click distribution
        if df['Clicks'].sum() > 0:
            fig, ax = plt.subplots(figsize=(10, 5))
            sorted_df = df.sort_values(
                'Clicks', ascending=True)
            colors = plt.cm.RdYlGn(
                sorted_df['Clicks'] /
                sorted_df['Clicks'].max()
            ) if sorted_df['Clicks'].max() > 0 \
              else ['#3498db'] * len(sorted_df)
            bars = ax.barh(
                sorted_df['Label'],
                sorted_df['Clicks'],
                color=colors,
                edgecolor='black'
            )
            for bar, val in zip(
                bars, sorted_df['Clicks']
            ):
                ax.text(
                    bar.get_width() + 0.1,
                    bar.get_y() + bar.get_height()/2,
                    str(val),
                    va='center',
                    fontsize=10,
                    fontweight='bold'
                )
            ax.set_title('Clicks per Link', fontsize=14)
            ax.set_xlabel('Number of Clicks')
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No clicks recorded yet.")

        # Summary table
        st.markdown("### Performance Summary")
        summary = df[['Label', 'Code',
                       'Clicks', 'Created']].copy()
        summary = summary.sort_values(
            'Clicks', ascending=False)
        st.dataframe(summary,
                     use_container_width=True,
                     hide_index=True)

# Tab 3 — My Links
with tab3:
    st.markdown("### All Your Links")

    if not links:
        st.info("No links yet. Create one first!")
    else:
        for code, data in sorted(
            links.items(),
            key=lambda x: x[1]['created'],
            reverse=True
        ):
            with st.expander(
                f"🔗 {data['label'][:40]} "
                f"— {data['clicks']} clicks"
            ):
                col1, col2, col3 = st.columns(3)
                col1.markdown(
                    f"**Short:** `rasdel7.short/{code}`")
                col2.markdown(
                    f"**Created:** {data['created']}")
                col3.markdown(
                    f"**Clicks:** {data['clicks']}")
                st.markdown(
                    f"**Original:** {data['original']}")

                # Simulate click
                if st.button(f"Simulate Click",
                             key=f"click_{code}"):
                    links[code]['clicks'] += 1
                    links[code]['click_log'].append(
                        datetime.now().strftime(
                            '%Y-%m-%d %H:%M'))
                    save_links(links)
                    st.success("Click recorded! ✅")
                    st.rerun()

                # Delete
                if st.button(f"🗑️ Delete",
                             key=f"del_{code}"):
                    del links[code]
                    save_links(links)
                    st.success("Link deleted!")
                    st.rerun()

# Tab 4 — QR Generator
with tab4:
    st.markdown("### 📱 QR Code Generator")
    st.markdown("Generate QR codes for any URL — "
                "no shortening required.")

    qr_url = st.text_input(
        "Enter URL for QR code:",
        placeholder="https://github.com/Rasdel7"
    )

    qr_size = st.slider(
        "QR Code Size:", 5, 15, 8)

    if st.button("Generate QR Code", type="primary"):
        if qr_url:
            qr  = qrcode.QRCode(
                version=1,
                error_correction=
                    qrcode.constants.ERROR_CORRECT_H,
                box_size=qr_size,
                border=4
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(
                fill_color="black",
                back_color="white"
            )
            buf = BytesIO()
            img.save(buf, format='PNG')
            buf.seek(0)

            col1, col2 = st.columns([1, 1])
            with col1:
                st.image(buf, width=300)
            with col2:
                st.markdown("### QR Details")
                st.metric("URL Length",
                          f"{len(qr_url)} chars")
                st.markdown(f"**URL:** {qr_url[:60]}")

                buf.seek(0)
                st.download_button(
                    "⬇️ Download QR Code",
                    buf,
                    "qrcode.png",
                    "image/png",
                    use_container_width=True
                )
        else:
            st.warning("Please enter a URL.")

st.markdown("---")
st.markdown(
    "Built by **Jyotiraditya** | "
    "URL Shortener with QR Code Generator"
)