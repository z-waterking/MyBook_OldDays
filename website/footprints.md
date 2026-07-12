# 足迹地图

> 从河津、运城到珠海、北京，再到地中海边。地图只标记原文能够确认的生活、求学、工作、旅行与中转足迹；私人住址均模糊到城市或城区级别。

<div class="footprints-page" data-source="website/footprints-data.json">
  <div class="footprints-summary">
    <span><strong>31</strong> 个中国地点</span>
    <span><strong>3</strong> 个西班牙地点</span>
    <span><strong>6</strong> 类人生足迹</span>
  </div>

  <div class="footprints-tabs" role="tablist" aria-label="地图范围">
    <button type="button" class="is-active" data-map-tab="china" role="tab" aria-selected="true">中国足迹</button>
    <button type="button" data-map-tab="world" role="tab" aria-selected="false">世界足迹</button>
  </div>

  <div id="footprints-map" class="footprints-map" role="region" aria-label="作者足迹交互地图"></div>
  <p class="footprints-map-note">点击标记查看地点、时期和来源文章。地图需要联网加载底图；下方列表始终可读。</p>

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
        <select id="footprints-filter">
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
    <div id="footprints-list" class="footprints-list" aria-live="polite"></div>
  </section>
</div>

<noscript>

## 无脚本阅读

- **山西：** 河津、运城、康杰中学、平遥古城、皇城相府
- **粤港澳：** 珠海、东澳岛、斗门、中山、佛山里水、广州、深圳、香港、澳门
- **北京与杭州：** 北京、798、杭州
- **旅途：** 华山、西安、凤凰、武汉、成都、青城山、峨眉山、厦门、阳朔、济南、上海、苏州
- **西班牙：** 马拉加、希布拉法罗城堡、内尔哈方向

</noscript>
