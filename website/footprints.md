# 足迹地图

> 从河津、运城到珠海、北京，再到地中海边。地图区分原文记述的生活、求学、工作、旅行与中转，以及明确标注的未抵达计划方向；私人住址均模糊到城市或城区级别。

<div class="footprints-page" data-source="website/footprints-data.json">
  <div class="footprints-summary">
    <span><strong>33</strong> 个中国地点</span>
    <span><strong>3</strong> 个西班牙地点</span>
    <span><strong>6</strong> 类人生足迹</span>
  </div>

  <div class="footprints-tabs" role="group" aria-label="地图范围">
    <button type="button" class="is-active" data-map-tab="china" aria-pressed="true" disabled>中国足迹</button>
    <button type="button" data-map-tab="world" aria-pressed="false" disabled>世界足迹</button>
  </div>

  <div class="footprints-map-shell">
    <div id="footprints-map" class="footprints-map" role="region" aria-label="作者足迹交互地图" aria-busy="true">
      <p class="footprints-map-status" role="status">正在加载地图与地点档案…</p>
    </div>
    <p class="footprints-map-hint">点击标记，打开背后的文章</p>
  </div>
  <p class="footprints-map-note">点击标记查看地点、时期和来源文章。连线表示人生阶段或计划方向，不是精确行走轨迹；内尔哈未抵达。地图需要联网加载底图；下方列表始终可读。</p>

  <div class="footprints-legend" aria-label="足迹类型">
    <span data-kind="life">长期生活</span>
    <span data-kind="study">求学</span>
    <span data-kind="work">工作</span>
    <span data-kind="choice">考试与选择</span>
    <span data-kind="travel">旅行</span>
    <span data-kind="transit">中转</span>
  </div>

  <section class="footprints-list-section">
    <div class="footprints-list-head">
      <p>地点档案</p>
      <label>筛选
        <select id="footprints-filter" disabled>
          <option value="all">全部足迹</option>
          <option value="life">长期生活</option>
          <option value="study">求学</option>
          <option value="work">工作</option>
          <option value="choice">考试与选择</option>
          <option value="travel">旅行</option>
          <option value="transit">中转</option>
        </select>
      </label>
    </div>
    <div id="footprints-list" class="footprints-list" aria-live="polite" aria-busy="true"></div>
  </section>
</div>

<details id="footprints-static-index" class="footprints-static-index">
  <summary>静态地点索引（离线或地图不可用时展开）</summary>
  <p><strong>黑龙江：</strong><a href="#/articles/合集-19-我在北京大厂实习/index.md">哈尔滨、雪乡</a></p>
  <p><strong>山西：</strong><a href="#/articles/合集-01-我在河津上幼儿园/index.md">河津</a>、<a href="#/articles/合集-03-我在运中念初中/index.md">运城</a>、<a href="#/articles/合集-05-我在康杰念高中（怀昔）/index.md">康杰中学</a>、<a href="#/articles/合集-08-我在珠海上大学（风途）/index.md">平遥古城、皇城相府</a></p>
  <p><strong>粤港澳：</strong><a href="#/articles/合集-06-我在珠海上大学（新序）/index.md">珠海、东澳岛</a>、<a href="#/articles/合集-08-我在珠海上大学（风途）/index.md">斗门、中山、深圳、香港、澳门</a>、<a href="#/articles/合集-11-我在佛山做家教/index.md">佛山里水</a>、<a href="#/articles/合集-13-我在广州做游戏/index.md">广州</a></p>
  <p><strong>工作与生活：</strong><a href="#/articles/合集-14-我在阿里做实习（推荐算法版）/index.md">杭州</a>、<a href="#/articles/合集-16-我在北京住合租屋/index.md">北京</a>、<a href="#/articles/合集-19-我在北京大厂实习/index.md">北京 798</a></p>
  <p><strong>国内旅途：</strong><a href="#/articles/合集-11-我在佛山做家教/index.md">华山</a>、<a href="#/articles/合集-08-我在珠海上大学（风途）/index.md">凤凰、武汉、成都、青城山、峨眉山、厦门、阳朔、上海、苏州、昆山与重庆</a>、<a href="#/articles/合集-09-我在珠海上大学（忽然之间）/index.md">济南</a>、<a href="#/articles/合集-18-我的第二次考公经历/index.md">西安</a></p>
  <p><strong>西班牙：</strong><a href="#/articles/合集-20-我在西班牙骑自行车/index.md">马拉加、希布拉法罗城堡、内尔哈方向</a></p>
  <p><strong>未定位到城市的旅行：</strong><a href="#/articles/合集-14-我在阿里做实习（推荐算法版）/index.md">江西探访ZC</a>、<a href="#/articles/散篇-17-意念“挥刀”/index.md">日本旅行</a>。原文未明确城市，不新增精确地点标记。</p>
</details>
