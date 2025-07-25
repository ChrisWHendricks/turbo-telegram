# Engineering Blog

A Jekyll-powered blog for sharing engineering insights, best practices, and lessons learned. This repository serves as a template for company-wide developer blogs.

## 🚀 Quick Start

### Prerequisites

- Ruby 2.7+ (recommended: 3.1)
- Bundler gem
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/blog.git
   cd blog
   ```

2. **Install dependencies**
   ```bash
   bundle install
   ```

3. **Start the development server**
   ```bash
   bundle exec jekyll serve
   ```

4. **View the blog**
   Open http://localhost:4000 in your browser

## 📝 Writing Posts

### Creating a New Post

1. Create a new file in `_posts/` with the format: `YYYY-MM-DD-title.md`
2. Add the required front matter:
   ```yaml
   ---
   layout: post
   title: "Your Post Title"
   date: YYYY-MM-DD HH:MM:SS -0000
   author: Your Name
   categories: [category1, category2]
   tags: [tag1, tag2]
   ---
   ```
3. Write your content in Markdown

### Writing Guidelines

- **Use clear, descriptive titles**
- **Include practical examples and code snippets**
- **Add relevant tags and categories**
- **Keep posts focused on a single topic**
- **Include a brief summary at the beginning**

## 🎯 Content Categories

- **Architecture**: System design, patterns, and decisions
- **Best Practices**: Coding standards, testing, and workflows
- **Tools & Technology**: Framework reviews and comparisons
- **Lessons Learned**: Post-mortems and retrospectives
- **Team Culture**: Collaboration and growth practices

## 🔧 Configuration

### Site Settings

Edit `_config.yml` to customize:
- Site title and description
- Author information
- Social links
- Navigation menu

### Adding Authors

1. Create a new file in `_authors/`: `username.md`
2. Add author information:
   ```yaml
   ---
   name: username
   display_name: Full Name
   bio: Brief bio
   email: author@company.com
   ---
   ```

## 🚢 Deployment

### GitHub Pages (Recommended)

This repository is configured for automatic deployment to GitHub Pages:

1. **Enable GitHub Pages** in repository settings
2. **Set source** to "GitHub Actions"  
3. **Push to main branch** - the site builds automatically

### Manual Deployment

```bash
# Build the site
bundle exec jekyll build

# Deploy _site/ directory to your hosting provider
```

## 🔍 Local Development Tips

### Preview Draft Posts
```bash
bundle exec jekyll serve --drafts
```

### Enable Live Reload
```bash
bundle exec jekyll serve --livereload
```

### Build for Production
```bash
JEKYLL_ENV=production bundle exec jekyll build
```

## 📁 Directory Structure

```
├── _authors/          # Author profiles
├── _includes/         # Reusable HTML components
├── _layouts/          # Page templates
├── _posts/           # Blog posts
├── _sass/            # Sass stylesheets
├── assets/           # CSS, JS, images
├── .github/workflows/ # GitHub Actions
├── _config.yml       # Jekyll configuration
├── Gemfile          # Ruby dependencies
└── index.md         # Homepage
```

## 🤝 Contributing

### For Team Members

1. **Fork this repository**
2. **Create a feature branch**: `git checkout -b post/your-topic`
3. **Write your post** following the guidelines above
4. **Submit a pull request** with a clear description

### Review Process

- All posts are reviewed by the engineering team
- Focus on technical accuracy and clarity
- Ensure examples are production-ready
- Verify all links and references

## 📊 Analytics & SEO

The blog includes:
- **Jekyll SEO Tag** for search engine optimization
- **RSS feed** for content syndication
- **Structured data** for rich snippets
- **Social media meta tags**

## 🛠️ Customization

### Styling

- Edit `_sass/` files for custom styles
- Modify `assets/main.scss` for global changes
- Use the Minima theme as a base

### Functionality

- Add plugins in `_config.yml`
- Create custom includes in `_includes/`
- Extend layouts in `_layouts/`

## 📋 Maintenance

### Regular Tasks

- Update Ruby gems: `bundle update`
- Review and merge contribution PRs
- Monitor site performance and uptime
- Archive old posts if necessary

### Troubleshooting

**Site not building?**
- Check the GitHub Actions log
- Validate YAML front matter
- Test locally first

**Styling issues?**
- Clear Jekyll cache: `bundle exec jekyll clean`
- Check Sass compilation errors
- Validate HTML markup

## 📞 Support

- **Technical Issues**: Create a GitHub issue
- **Content Questions**: Contact the engineering team
- **Access Problems**: Check with repository admins

---

## 🎉 Getting Started Checklist

- [ ] Clone the repository
- [ ] Update `_config.yml` with your information
- [ ] Customize the homepage (`index.md`)
- [ ] Write your first blog post
- [ ] Enable GitHub Pages in repository settings
- [ ] Share the blog URL with your team

**Ready to start blogging!** 🚀