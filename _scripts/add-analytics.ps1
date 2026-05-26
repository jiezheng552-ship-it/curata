$analyticsSnippet = @'
<!-- Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-XXXXXXXXXX');
</script>
<script>
var _hmt = _hmt || [];
(function() {
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
})();
</script>
'@

$files = @(
  "D:\新建文件夹\cursor\curata\index.html",
  "D:\新建文件夹\cursor\curata\about.html",
  "D:\新建文件夹\cursor\curata\newsletter.html",
  "D:\新建文件夹\cursor\curata\recommends.html",
  "D:\新建文件夹\cursor\curata\blog\index.html",
  "D:\新建文件夹\cursor\curata\blog\post.html",
  "D:\新建文件夹\cursor\curata\blog\macbook-air-m4.html",
  "D:\新建文件夹\cursor\curata\blog\stagg-ekg-review.html",
  "D:\新建文件夹\cursor\curata\blog\kindle-scribe-2025.html",
  "D:\新建文件夹\cursor\curata\blog\xiaomi-air-purifier-4-pro.html",
  "D:\新建文件夹\cursor\curata\blog\fujifilm-xt6.html"
)

foreach ($file in $files) {
  $content = Get-Content -Path $file -Raw -Encoding UTF8
  if ($content -notmatch 'Google Analytics|googletagmanager') {
    $content = $content -replace '</head>', "$analyticsSnippet`r`n</head>"
    [System.IO.File]::WriteAllText($file, $content, [System.Text.UTF8Encoding]::new($false))
    Write-Output "Added analytics to: $file"
  } else {
    Write-Output "Already has analytics: $file"
  }
}
