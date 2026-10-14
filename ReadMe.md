# iNdra Page Template: This is a Website / GitHub Page Template for Research Papers / Academic Papers [Free] [v2]

> 🚀 **Demo Page**: [https://indramal.github.io/iNdra-GitHub-Page-Template-For-Resarch/](https://indramal.github.io/iNdra-GitHub-Page-Template-For-Resarch/)

---

> # ⚡ ZERO-CODE RESEARCH PAPER WEBSITE TEMPLATE
> ### **NO HTML, CSS, OR CODING KNOWLEDGE REQUIRED!**  
> Simply edit a single text file (`data.yaml`) to publish a world-class, responsive research paper website on GitHub Pages instantly.

---

A clean, modern, responsive website and GitHub Pages template designed for research papers and academic projects. **Version 2 introduces a zero-code, YAML-driven architecture** so non-technical researchers can publish their research pages effortlessly by editing a single text file (`data.yaml`)!

---

## ✨ Features (v2)

- ⚡ **Zero-Code YAML Data Config (`data.yaml`)**: Edit text, authors, buttons, affiliations, and paper sections without opening HTML, CSS, or JS files!
- 🚀 **Instant Skeleton Loading**: Modern shimmer animations while loading data.
- 📌 **Modular Components**: Easily add any component into any section:
  - 🖼️ **Image Carousel & Gallery** (Auto-sliding responsive slideshow)
  - 🎥 **Video Carousel & Gallery** (Multiple video slideshow)
  - 📺 **YouTube Video & Playlist Embeds**
  - 📋 **Custom Point Style Lists** (Bullet •, Numbered 1.2.3, Checkmarks ✅, Arrows ➡️, Stars ⭐, Circles ◦, Squares ▪, None)
  - 💻 **Custom HTML Component** (Embed raw HTML tables, alert boxes, badges, or custom widgets)
- 📂 **Subsections Support**: Easily break down sections into sub-headings (`subsections:`) with their own content, lists, and components.
- ⚙️ **Customizable UI Settings in YAML**:
  - `max_width`: Custom page width (e.g. `"1024px"`, `"1200px"`)
  - `nav_shadow`: Toggle top navigation elevation shadow (`true`/`false`)
  - `nav_scroll_highlight`: Auto-highlight matching menu links on scroll
  - `nav_highlight_color`: Custom highlight color (e.g. `"#3498db"`)
  - `show_bibtex_button`: Toggle BibTeX action button
  - Custom button background colors & label texts
- 📜 **One-Click BibTeX Clipboard Copy**: Readers can copy paper citations with a single click.
- 📱 **100% Full-Width Responsive Layout**: Full-width sticky navigation bar and full-width edge-to-edge footer.
- 🔄 **Dual Editing Mode**: Prefer traditional HTML editing? Set `const USE_YAML_DATA = false;` in `index.html` to switch back to static HTML anytime.

---

## 🚀 Quick Setup (For Non-Technical Users)

### Step 1: Fork or Download this Repository
- Click **Use this template** or **Fork** at the top right of this GitHub page, or download the ZIP.

### Step 2: Edit `data.yaml`
- Open `data.yaml` in your browser or any text editor.
- Fill in your paper title, authors, affiliations, email addresses, project link buttons, abstract, and sections.

### Step 3: Enable GitHub Pages
1. Go to your repository **Settings** → **Pages**.
2. Under **Source**, select `Deploy from a branch` and choose `main` (or `master`) branch / `(root)` folder.
3. Click **Save**. GitHub will automatically build and publish your paper page!

---

## 🛠️ How to Edit `data.yaml`

All content is configured inside `data.yaml`. Here is a quick reference:

### 1. Paper Info & Header
```yaml
paper_title: "Your Research Paper Title"

authors:
  - name: "First Author"
    superscript: "1"
    url: "https://author-website.com"
  - name: "Second Author"
    superscript: "2"
    url: "#"

affiliations:
  - index: "1"
    name: "University Name 1"
  - index: "2"
    name: "University Name 2"

equal_contribution_note: "* Equal Contribution"

conference_badges:
  - "📌 Published at CVPR 2024 (Oral Talk)"

header_note: "Optional custom note after conference badges"
```

### 2. Resource Buttons
```yaml
buttons:
  - label: "Paper"
    icon: "📄"
    url: "https://arxiv.org/abs/..."
    color: "" # Optional custom color
  - label: "Code"
    icon: "💻"
    url: "https://github.com/..."

show_bibtex_button: true
```

### 3. Sections, Subsections & Component Usage
```yaml
sections:
  - id: "abstract"
    title: "Abstract"
    nav_label: "Abstract"
    content: "Your paper abstract text..."
    components:
      - type: "youtube_video"
        title: "Demo Video"
        url: "https://www.youtube.com/embed/ysFav0b472w"

  - id: "methodology"
    title: "Methodology"
    nav_label: "Methodology"
    content: "Overview of your method."
    subsections:
      - title: "1. Feature Extraction"
        content: "Details about feature extraction..."
        list_type: "check"
        list:
          - "Step 1: Preprocessing"
          - "Step 2: Normalization"
        components:
          - type: "image_carousel"
            title: "Pipeline Gallery"
            images:
              - "Assets/Photo1.jpg"
              - "Assets/Photo2.jpg"
```

### 4. Page Settings
```yaml
settings:
  max_width: "1024px"          # Custom content width
  nav_shadow: true             # Show top navbar shadow
  nav_scroll_highlight: true   # Highlight menu link on scroll
  nav_highlight_color: ""      # Custom highlight color
  theme_toggle_text: "Toggle Dark Mode"
  copy_bibtex_text: "Copy to Clipboard"
  scroll_top_text: "⬆"
```

---

## 🧩 Modular Components & Parameter Guide

You can add any of the following components inside `components:` under any section or subsection in `data.yaml`:

### 1. YouTube Video Embed (`youtube_video`)
Embed a single YouTube video with an optional title and description text.
- **Parameters**: `type`, `title`, `url`, `description`
```yaml
      - type: "youtube_video"
        title: "Demo Video"
        url: "https://www.youtube.com/embed/ysFav0b472w"
        description: "Short explanation paragraph of the video."
```

### 2. YouTube Playlist Embed (`youtube_playlist`)
Embed an entire YouTube playlist player.
- **Parameters**: `type`, `title`, `url`
```yaml
      - type: "youtube_playlist"
        title: "Video Playlist"
        url: "https://www.youtube.com/embed/videoseries?list=PL95lT3XlM14SgZHmmKn1mGSAAQc8ycq8v"
```

### 3. Image Carousel / Gallery (`image_carousel`)
Create an interactive sliding image carousel.
- **Parameters**: `type`, `title`, `images`
```yaml
      - type: "image_carousel"
        title: "Image Gallery"
        images:
          - "Assets/Photo1.jpg"
          - "Assets/Photo2.jpg"
          - "Assets/Photo3.jpg"
```

### 4. Video Carousel / Gallery (`video_carousel`)
Create an interactive sliding carousel for multiple YouTube videos.
- **Parameters**: `type`, `title`, `videos`
```yaml
      - type: "video_carousel"
        title: "Video Gallery"
        videos:
          - "https://www.youtube.com/embed/Bhg3uOx9ZPw"
          - "https://www.youtube.com/embed/xjRALKy6Ajw"
```

### 5. List Component (`list`)
Add bulleted, numbered, or styled lists into sections or subsections.
- **Parameters**: `type`, `title`, `list_type`, `list`
- **List Style Options (`list_type`)**:
  - `"bullet"`: Standard bullet points (•)
  - `"number"`: Numbered list (1, 2, 3...)
  - `"check"`: Checkmarks (✅)
  - `"arrow"`: Arrows (➡️)
  - `"star"`: Stars (⭐)
  - `"circle"`: Hollow circles (◦)
  - `"square"`: Filled squares (▪)
  - `"none"`: Plain text list without bullets
```yaml
      - type: "list"
        title: "Key Highlights"
        list_type: "check"
        list:
          - "First key highlight"
          - "Second key highlight"
```

### 6. Custom HTML Component (`custom_html`)
Embed custom raw HTML code (tables, alert boxes, badges, or custom widgets).
- **Parameters**: `type`, `title`, `html`
```yaml
      - type: "custom_html"
        title: "Custom Alert Box"
        html: |
          <div style="background: #eef6ff; padding: 12px; border-radius: 6px;">
            <p>Add custom HTML code or widgets here!</p>
          </div>
```

---

## 💡 Helpful Tools & Tips

Here are free online tools to assist with editing, validating YAML syntax, and optimizing paper images:

- 🔍 **YAML Syntax Checker / Validator**: Verify your `data.yaml` formatting and check indentation:
  - [YAML Checker](https://yamlchecker.com/)
  - [YAML Lint](https://www.yamllint.com/)
- 🖼️ **Image Compression Tool**: Compress your figures & paper photos for ultra-fast page loading:
  - [TinyPNG](https://tinypng.com/)
- ✂️ **Image Background Removal Tool**: Effortlessly remove image backgrounds for figures or author headshots:
  - [Remove.bg](https://www.remove.bg/)
- 📊 **HTML Table Generator**: Easily generate clean HTML table code for paper results or benchmark comparisons (use with `custom_html` component):
  - [DivTable HTML Table Generator](https://divtable.com/generator/)

> 📌 **SEO Tip for YAML Mode**: When using `data.yaml` mode, search engine crawlers (Google, Bing) and social media platforms (Twitter/X, LinkedIn) read the HTML metadata tags directly from `index.html`. For optimal Search Engine Optimization (SEO) and social media link previews, remember to update the `<title>`, `<meta name="description">`, and `<meta property="og:title">` tags at the top of `index.html`!

---

## 💻 Technical Users (Manual HTML Mode)

If you prefer to edit static HTML directly:
1. Open `index.html`.
2. Change `<script>const USE_YAML_DATA = true;</script>` to `<script>const USE_YAML_DATA = false;</script>`.
3. Uncomment the `STATIC HTML EDIT METHOD START` block in `index.html` and edit your HTML directly!

---

## 🔍 Search Keywords & SEO Index

`research paper website template` • `academic website template` • `github pages research template` • `arxiv paper website template` • `zero-code research page` • `yaml driven academic website` • `cvpr paper website template` • `icml paper website template` • `neurips paper website template` • `eccv paper website` • `aaai paper website` • `conference paper template` • `project page template` • `academic portfolio template` • `research paper showcase` • `paper demo video embed` • `bibtex copy button template` • `dark mode paper template` • `responsive academic website` • `github pages paper showcase` • `academic project website` • `research paper github page` • `free academic template`

---

Please send me feedback on [GitHub Issues](https://github.com/indramal/iNdra-GitHub-Page-Template-For-Resarch/issues).

> Made with ❤️ by [Indramal](https://github.com/indramal)
