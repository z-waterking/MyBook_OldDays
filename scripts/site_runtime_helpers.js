(function exposeSiteRuntimeHelpers(global) {
  'use strict';

  function normalizeSiteHash(value) {
    var normalized = String(value || '');
    try { normalized = decodeURI(normalized); } catch (error) {}
    return normalized
      .replace(/\?id=.*$/, '')
      .replace(/\.md$/, '')
      .replace(/\/$/, '');
  }

  function articleContextFromHash(value) {
    var route = normalizeSiteHash(value);
    var original = route.match(/^#\/articles\/([^/]+)\/(index|review)$/);
    var edited = route.match(/^#\/ai-edited-articles\/(合集|散篇)\/([^/]+)\/(index|notes)$/);
    var articleName;
    var page;
    if (original) {
      articleName = original[1];
      page = original[2] === 'review' ? 'review' : 'original';
    } else if (edited) {
      articleName = edited[2];
      page = edited[3] === 'notes' ? 'notes' : 'edited';
    } else {
      return null;
    }
    return {
      articleName: articleName,
      category: articleName.indexOf('合集-') === 0 ? '合集' : '散篇',
      page: page
    };
  }

  function sidebarArticleContextFromHash(value) {
    var context = articleContextFromHash(value);
    if (!context) return null;
    var labels = {
      original: '原文',
      review: '文章评价',
      edited: 'AI改稿',
      notes: '改稿说明'
    };
    return {
      articleName: context.articleName,
      targetHash: '#/articles/' + context.articleName + '/index',
      label: labels[context.page]
    };
  }

  global.siteRuntimeHelpers = {
    normalizeSiteHash: normalizeSiteHash,
    articleContextFromHash: articleContextFromHash,
    sidebarArticleContextFromHash: sidebarArticleContextFromHash
  };
}(typeof window === 'undefined' ? globalThis : window));
