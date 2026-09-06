/**
 * 个人网站脚本 — 极简交互
 */

(function () {
  'use strict';

  // === 回到顶部按钮显隐 ===
  const backToTop = document.querySelector('.back-to-top');
  if (backToTop) {
    let ticking = false;

    function updateBackToTop() {
      const scrollY = window.scrollY || window.pageYOffset;
      if (scrollY > 400) {
        backToTop.classList.add('visible');
      } else {
        backToTop.classList.remove('visible');
      }
      ticking = false;
    }

    window.addEventListener('scroll', function () {
      if (!ticking) {
        requestAnimationFrame(updateBackToTop);
        ticking = true;
      }
    }, { passive: true });

    // 初始状态
    updateBackToTop();
  }

  // === 平滑滚动到锚点（优雅降级：scroll-behavior 已处理标准情况） ===
  // 对于不支持 scroll-behavior 的老浏览器做 polyfill
  if (!('scrollBehavior' in document.documentElement.style)) {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
      anchor.addEventListener('click', function (e) {
        var targetId = this.getAttribute('href');
        if (!targetId || targetId === '#') return;
        var target = document.querySelector(targetId);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });
  }

  // === 页面加载完成 ===
  console.log(
    '%c Harvey %c个人网站已就绪',
    'color: #d4a574; font-size: 1.2em; font-weight: bold;',
    'color: #8b949e;'
  );
  console.log(
    '%cBuilt with %c❤️ %c+ vanilla HTML/CSS/JS',
    'color: #8b949e;',
    'color: #f85149;',
    'color: #8b949e;'
  );

})();
