<#
  Curata — 一键部署脚本
  支持: Surge.sh / Netlify / Vercel / GitHub Pages
  用法: .\deploy.ps1
#>

$ErrorActionPreference = "Stop"
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$SITE_NAME = "curata"

Write-Host @"
╔═══════════════════════════════════════╗
║   Curata — 一键部署                    ║
╚═══════════════════════════════════════╝
"@ -ForegroundColor Cyan
Write-Host "项目目录: $PROJECT_DIR`n" -ForegroundColor Gray

# ─── Check available deploy tools ───
$tools = @{}
$globalOption = -1

function Check-Tool($name, $cmd) {
    $null = Get-Command $cmd -ErrorAction SilentlyContinue
    $tools[$name] = $?
    if ($tools[$name]) {
        Write-Host "  [✓] $name 已安装" -ForegroundColor Green
    } else {
        Write-Host "  [✗] $name 未安装" -ForegroundColor DarkYellow
    }
}

Write-Host "检查部署工具..." -ForegroundColor Yellow
Check-Tool "Surge"     "surge"
Check-Tool "Netlify"   "netlify"
Check-Tool "Vercel"    "vercel"
Check-Tool "gh-pages"  "gh-pages"

# ─── Menu ───
Write-Host "`n选择部署方式:" -ForegroundColor Cyan
$options = @()

if ($tools["Surge"]) {
    $options += "Surge.sh — 最快最简，单命令部署到 surge.sh"
}
if ($tools["Netlify"]) {
    $options += "Netlify — 自动 HTTPS + 持续部署，推荐生产使用"
}
if ($tools["Vercel"]) {
    $options += "Vercel — 全球 CDN，自动 HTTPS"
}
if ($tools["gh-pages"]) {
    $options += "GitHub Pages — 推送到 gh-pages 分支"
}
$options += "退出"

for ($i = 0; $i -lt $options.Count; $i++) {
    Write-Host "  [$($i+1)] $($options[$i])"
}

$choice = Read-Host "`n请输入序号 (1-$($options.Count))"
$index = [int]$choice - 1

if ($index -lt 0 -or $index -ge $options.Count -or $options[$index] -eq "退出") {
    Write-Host "已取消" -ForegroundColor Gray
    exit 0
}

$selected = $options[$index]

# ─── Deploy ───
Write-Host "`n>>> 部署中..." -ForegroundColor Yellow

if ($selected -like "Surge*") {
    # Surge.sh deploy
    $domain = Read-Host "`n自定义域名 (留空使用 $SITE_NAME.surge.sh)"
    if ([string]::IsNullOrWhiteSpace($domain)) {
        $domain = "$SITE_NAME.surge.sh"
    }
    Write-Host "部署到 $domain ..." -ForegroundColor Green
    surge $PROJECT_DIR $domain
}

elseif ($selected -like "Netlify*") {
    # Netlify deploy
    if (-not (Test-Path "$PROJECT_DIR\netlify.toml")) {
        @"
[build]
  publish = "."
"@ | Set-Content -Path "$PROJECT_DIR\netlify.toml" -Encoding UTF8
        Write-Host "  [i] 已创建 netlify.toml" -ForegroundColor Gray
    }
    Write-Host "部署到 Netlify..." -ForegroundColor Green
    netlify deploy --prod --dir $PROJECT_DIR
}

elseif ($selected -like "Vercel*") {
    # Vercel deploy
    if (-not (Test-Path "$PROJECT_DIR\vercel.json")) {
        @'
{
  "name": "curata",
  "version": 2,
  "builds": [
    { "src": "/*", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/css/(.*)", "dest": "/css/$1" },
    { "src": "/js/(.*)", "dest": "/js/$1" },
    { "src": "/blog/(.*)", "dest": "/blog/$1" },
    { "src": "/assets/(.*)", "dest": "/assets/$1" },
    { "src": "/(.*)", "dest": "/$1" }
  ]
}
'@ | Set-Content -Path "$PROJECT_DIR\vercel.json" -Encoding UTF8
        Write-Host "  [i] 已创建 vercel.json" -ForegroundColor Gray
    }
    Write-Host "部署到 Vercel..." -ForegroundColor Green
    vercel --prod $PROJECT_DIR
}

elseif ($selected -like "GitHub*") {
    # GitHub Pages
    Write-Host "推送到 GitHub Pages (gh-pages 分支)..." -ForegroundColor Green
    $repo = Read-Host "GitHub 仓库地址 (如 user/repo，留空则只构建)"

    if (-not [string]::IsNullOrWhiteSpace($repo)) {
        # Check if git is initialized
        if (-not (Test-Path "$PROJECT_DIR\.git")) {
            git init
            git checkout -b main
        }

        if (-not (Test-Path "$PROJECT_DIR\.gitignore")) {
            "node_modules`n.DS_Store`n*.log" | Set-Content -Path "$PROJECT_DIR\.gitignore" -Encoding UTF8
        }

        # Use npx gh-pages
        npx gh-pages --dist $PROJECT_DIR --branch gh-pages --message "Deploy Curata $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        Write-Host "  [✓] 已部署到 https://$repo.github.io/curata/" -ForegroundColor Green
    } else {
        Write-Host "请手动运行: npx gh-pages --dist $PROJECT_DIR" -ForegroundColor DarkYellow
    }
}

# ─── Done ───
Write-Host "`n=== 部署完成 ===" -ForegroundColor Cyan
Write-Host "网站目录: $PROJECT_DIR" -ForegroundColor Gray
Write-Host ""
Write-Host "赚钱方式:" -ForegroundColor Green
Write-Host "  1. 替换 affiliate 链接为你的联盟营销账号链接" -ForegroundColor Gray
Write-Host "  2. 替换文章内容为你的原创评测文章" -ForegroundColor Gray
Write-Host "  3. 接入 Google AdSense 或百度联盟放广告" -ForegroundColor Gray
Write-Host "  4. 添加更多推荐商品品类扩大覆盖" -ForegroundColor Gray
Write-Host "  5. 通过邮件订阅积累读者，后续可推出付费内容" -ForegroundColor Gray
Write-Host ""
Write-Host "加油！ Curata 已经开始为你工作了。" -ForegroundColor Green
