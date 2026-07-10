#!/usr/bin/env node

import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { cwd } from 'node:process';

const ROOT = cwd();
const ARTICLES_DIR = join(ROOT, 'articles');
const AI_DIR = join(ROOT, 'ai-edited-articles');
const TODAY = new Date().toISOString().slice(0, 10);

const args = new Set(process.argv.slice(2));
const FORCE = args.has('--force');
const REFRESH_GENERATED = args.has('--refresh-generated');

function parseFrontmatter(content) {
  const meta = {};
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return meta;
  for (const line of match[1].split(/\r?\n/)) {
    const m = line.match(/^([^:]+):\s*(.*)$/);
    if (!m) continue;
    let value = m[2].trim();
    if (value.startsWith('"') && value.endsWith('"')) {
      value = value.slice(1, -1).replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\\\/g, '\\');
    }
    meta[m[1].trim()] = value;
  }
  return meta;
}

function yamlQuote(value) {
  return `"${String(value || '').replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\r/g, '\\r').replace(/\n/g, '\\n')}"`;
}

function stripBoilerplate(content) {
  return content
    .replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n*/, '')
    .trimStart()
    .replace(/^#\s+.*\r?\n+/, '')
    .trimStart()
    .replace(/^>\s*作者:[^\n]*\r?\n+/, '')
    .trimStart()
    .replace(/<p><img class="article-cover"[\s\S]*?<\/p>\r?\n*/g, '')
    .replace(/\r\n/g, '\n')
    .replace(/\n---\n\*原文链接:[\s\S]*$/m, '')
    .trim();
}

function rebaseImages(body, dirName) {
  return body
    .replace(/!\[([^\]]*)\]\(images\/([^)]*)\)/g, `![$1](articles/${dirName}/images/$2)`)
    .replace(/src="images\/([^"]*)"/g, `src="articles/${dirName}/images/$1"`);
}

function groupOf(dirName) {
  if (dirName.startsWith('散篇-')) return '散篇';
  if (dirName.startsWith('合集-')) return '合集';
  return '其他';
}

function isGeneratedDraft(content) {
  return /^edit_round:\s*"v1"\s*$/m.test(content)
    && /^status:\s*"AI 修改稿"\s*$/m.test(content);
}

function latestReviewName(files) {
  return files.includes('review.md') ? 'review.md' : undefined;
}

function sectionAfter(review, headings) {
  for (const heading of headings) {
    const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const match = review.match(new RegExp(`##[^\n]*${escaped}[^\n]*\n([\\s\\S]*?)(?=\n##|$)`));
    if (match) return match[1].trim();
  }
  return '';
}

function plainExcerpt(markdown, limit = 260) {
  const text = markdown
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/[#>*_`~|]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  return text.length > limit ? `${text.slice(0, limit)}...` : text;
}

function parseScore(ranking, dirName) {
  const encoded = encodeURI(`articles/${dirName}/`);
  const raw = `articles/${dirName}/`;
  for (const line of ranking.split(/\r?\n/)) {
    if (!line.includes(raw) && !line.includes(encoded)) continue;
    return line.match(/\|\s*\d+\s*\|\s*\*\*([^*]+)\*\*/)?.[1] || '';
  }
  return '';
}

function titleWithoutPrefix(dirName, title) {
  return title || dirName.replace(/^(合集|散篇)-\d{2}-/, '');
}

function generateClosing(dirName, title) {
  if (dirName === '散篇-05-剿贼（一）' || dirName === '散篇-06-元亨利' || dirName === '散篇-12-请出示证件') return '';
  if (dirName.includes('幼儿园')) return '很多年后再回头看，幼儿园留下来的并不是完整故事，而是一堆会突然亮起来的小东西：博物馆后面的坡、蹦床、老师的声音、还有小孩子以为天塌了的大事。它们都不宏大，但它们确实把一个人最早的底色涂出来了。';
  if (dirName.includes('小学')) return '小学的日子像一张摊开的旧地图，每一条路都不长，但每一条路都能走回去。那时候以为长大很远，后来才知道，很多判断、胆量和怕黑的方式，都是那几年悄悄定下来的。';
  if (dirName.includes('初中')) return '初中像一段夹在童年和青春之间的走廊。人还没有真正长大，却已经开始学着离家、学着比较、学着在集体里找到自己的位置。现在回头看，那些当时没觉得重要的早操、电话卡、饭票和宿舍夜话，反倒最能证明那几年真的存在过。';
  if (dirName.includes('拾初')) return '如果说后来的“怀昔”是把记忆往深处捞，那么“拾初”就是先把这些人的名字一个个喊回来。青春不是一上来就燃烧的，它先是点名、分座位、互相试探，然后某一天忽然发现，原来这群人已经成了自己故事里绕不开的人。';
  if (dirName.includes('大学') || dirName.includes('珠海')) return '后来再想起珠海，最先出现的往往不是某个宏大的选择，而是湿热的风、校车、海边、宿舍和那些不太体面的犹豫。大学真正教会人的东西，很多不在课表里，而在一次次走错路之后，还得继续往前走。';
  if (dirName.includes('课程')) return '所以包装工程这几个字，后来在我这里不再只是一个专业名。它更像一种提醒：很多东西的价值，取决于你怎么理解、怎么摆放、怎么给它一个能被看见的外壳。人也差不多。';
  if (dirName.includes('家教')) return '后来我再给别人讲东西时，总会想起里水那些晚上。讲题当然重要，但更重要的是看见一个人卡在哪里，愿不愿意陪他在那里多站一会儿。教育这件事，说到底不是把答案塞过去，而是把人从不会里慢慢领出来。';
  if (dirName.includes('考研究生')) return '考研这件事后来改变了很多东西，但身处其中的时候，它只是每天坐下、翻书、做题、怀疑自己，然后第二天继续。命运的琴弦并不是被某个宏大瞬间拨动的，它常常是在一个小城的傍晚，被人一页一页翻出来的。';
  if (dirName.includes('游戏')) return '广州那段时间并没有把我变成什么传奇人物，但它让我第一次真正看见了工作、城市和年轻人的临时生活。很多人短暂地聚在一起，吃饭、加班、吐槽、换工作，然后散掉。后来再想，能在那样的日子里留下几个具体的人，已经算是命运开恩。';
  if (dirName.includes('阿里做实习')) return '那个夏天最珍贵的地方，不在于大厂光环，而在于我终于看见光环里面也是普通人：有人认真做事，有人一起玩闹，有人递来水果，也有人在热闹散场后各自沉默。所谓实习，就是一边看世界，一边看自己到底想不想成为其中一员。';
  if (dirName.includes('闲鱼')) return '闲鱼教给我的，不只是怎么卖东西，而是怎么理解交易里的人。每一次砍价、爽约、成交和反悔，背后都有一点人性的小算盘。看多了以后，倒也不愤怒了，只觉得世界运行起来，确实不全靠道理。';
  if (dirName.includes('合租屋')) return '后来搬过很多次家，才明白房子不只是房子。它会记录一个人的狼狈、警惕、报复心和一点点尊严。合租屋最厉害的地方在于，它让所有人的生活边界挤在一起，然后逼着你学会怎么保护自己。';
  if (dirName.includes('初次考公')) return '现在再看那次失败，我反倒觉得它不像一次考试，更像一次命运安排的体测。它把我的侥幸、犹豫、理想和身体极限全都拎出来，放在同一个下午审了一遍。审完以后，路没有立刻变清楚，但我确实再也不是原来的我了。';
  if (dirName.includes('第二次考公')) return '有些选择之所以难，不是因为不知道哪条路更稳，而是知道以后依然迈不开腿。北京西站那一刻，我放弃的不是一张车票，而是一种别人看起来更像正确答案的人生。至于对不对，只能后来慢慢承担。';
  if (dirName.includes('大厂实习')) return '很多年后再看那段大厂实习，最动人的地方并不是我拿到了什么机会，而是我终于承认，选择本身也会犯错。年轻时以为重要的是选对，后来才知道，选错以后还能继续往前走，也是一种本事。';
  if (dirName.includes('西班牙')) return '旅行最好的部分，不是证明自己去过多远的地方，而是某个瞬间忽然发现，自己真的在路上。海风、芬达、自行车和异国清晨会过去，但身体记住了那种轻盈。以后日子再重，也能想起自己曾经这样骑出去过。';
  if (dirName.includes('音乐')) return '音乐最神奇的地方，是它会替人保存一些自己都保管不好的时间。多年以后，一首歌响起来，当时的人、路、天气和心情就会自动归位。它们不是背景音，而是人生某些章节的索引。';
  if (dirName.includes('圣诞')) return '很多轻飘飘的日子，当时看不出意义，后来反而变得可爱。圣诞前夕并不一定要发生大事，几个朋友、一点魔术、几句闲话，就足够证明那时候的生活还松弛，还能被一点小把戏逗笑。';
  if (dirName.includes('小记二十有九')) return '二十九岁并不是一个轰轰烈烈的年纪。它更像一场雪后的通勤：知道浪漫还在，但第一反应已经是别滑倒、别迟到、电脑别摔坏。人就是这样一点点长大的，不是突然成熟，而是快乐和风险开始同时出现。';
  if (dirName.includes('阿里奇妙')) return '梦从一个花名开始，也从一个花名结束。后来再想那段日子，最珍贵的并不是阿里这个名字，而是那些短暂出现过的人。大家像在同一个梦里互相打了个招呼，醒来以后，各自赶路。';
  if (dirName.includes('读研读废')) return '所以读研读废的结果，并不是一无所获。只是收获的东西和招生简章上写得不太一样。它没有让人立刻成为学术新星，但让人熟练掌握了现代生活的许多旁门左道。某种意义上，也算复合型人才。';
  if (dirName.includes('男朋友')) return '当然，以上方案只适用于技术排障。感情系统最麻烦的地方在于，它没有统一文档，也没有稳定接口。真要长期无响应，建议及时止损，毕竟青春不是后台服务，不能一直挂起等待。';
  if (dirName.includes('张雪峰')) return '死亡真正可怕的地方，是它让一切计划都显得有点可笑。我们当然还要努力、赚钱、赶路，但也要偶尔停一下，看看身边的人还在不在，自己还喜不喜欢现在的生活。毕竟人生不是项目排期，没有谁保证一定能发到最终版。';
  if (dirName.includes('vibe coding')) return 'AI 可以接管很多操作，但接管不了一个人如何安放自己的意义感。写代码也好，写文章也好，最怕的不是工具变强，而是人突然不知道自己还想表达什么。虚无感大概就从这里开始。';
  if (dirName.includes('leader')) return '职场里真正让人疲惫的，往往不是工作本身，而是那些打着管理名义的消耗。后来我离开时舍不得很多东西，但唯独不舍不得这种关系。人总要学会从一段坏关系里走出去，哪怕它曾经披着成长的外衣。';
  if (dirName.includes('工位')) return '所以我舍不得的不是公司，真不是。公司太大了，大到它不会记得一个普通人坐过哪里。可工位会记得。杯子、抽纸、显示器、椅子和那些摸鱼时刻，凑在一起，才像一个人在城市里临时搭起来的小窝。';
  if (dirName.includes('意念')) return '很多人以为幻想是逃避现实，其实幻想有时候是现实的预演。人在脑海里挥过很多次刀，真到了现实里，未必会更勇敢，但至少知道自己害怕什么。能把害怕想清楚，也算一种修炼。';
  if (dirName.includes('丧尸')) return '当然，现实里大概率不会有丧尸。但城市里那些墙、树、车顶、天桥和桥洞，依然值得观察。它们提醒我们，很多安全感不是灾难来临时突然长出来的，而是平时多看一眼、多想一步攒下来的。';
  return `后来再看《${title}》，最该保留下来的不是事件本身，而是事件里那个当时的我。人写回忆，写到最后，其实都是在给过去的自己留一个座位。`;
}

const customBodies = new Map([
  ['散篇-07-面试的艺术', ({ dirName }) => `面试是有艺术的。\n\n以前我觉得面试就是问答。面试官问，你答。答得上来，进入下一轮；答不上来，回去继续投简历。后来经历多了才发现，不是这样的。面试更像两拨人互相试探：一边假装自己这里前途无量，一边假装自己能力无边。大家都很真诚，真诚地表演。\n\n真正的面试高手，不一定每道题都会，但一定要让人感觉他会。不会也不能沉默太久，沉默超过十秒，空气里就会出现一种淡淡的死亡气息。你可以说“我先确认一下问题”，可以说“我从两个角度回答”，甚至可以说“这个点我之前了解得不深，但我会这样拆”。总之不能让场面掉到地上。\n\n当然，面试官也有艺术。有的面试官像审犯人，开口就是“你这个项目有什么难点”。我心想，难点就是我现在坐在这里，努力把一个并不复杂的项目讲得像攻克了人类文明难题。有的面试官像老中医，先不说话，盯着你看，仿佛能从你的简历里摸出脉象。还有的面试官非常温柔，温柔到你以为自己稳了，结果三天后收到感谢信。\n\n最折磨人的，是那种开放性问题。比如“你怎么看待团队合作”。这题当然不能说我怎么看，我用眼睛看。也不能说团队合作就是别人别拖我后腿。标准答案是先尊重、再沟通、最后共同推进。可现实里团队合作往往是：一个人写方案，一个人提意见，一个人已读不回，一个人负责在群里发“辛苦大家”。\n\n所以面试的艺术，归根结底是分寸。不能太老实，太老实显得没准备；不能太油，太油显得不可靠。不能把自己说得太弱，别人不敢要；也不能把自己说得太强，别人会追问。最好的状态，是让对方相信：这个人还有潜力，而且这个潜力暂时还没有贵到离谱。\n\n请欣赏。\n\n![](articles/${dirName}/images/001.png)\n\n如果面试结束后，你觉得自己发挥得很好，先别急着庆祝。人在面试后的自我感觉，和考试后对答案前的自信差不多，都有一定玄学成分。真正的艺术不是当场把话说漂亮，而是被拒之后还能继续投下一家。毕竟江湖很大，此处不留人，自有下一轮笔试。`],
  ['散篇-08-412之趣言趣闻', ({ dirName }) => `有些话离开了具体的人和场景，就会变得莫名其妙。\n\n所以整理“412之趣言趣闻”这种东西，本质上是在给一群人的共同生活做切片。外人看了可能一头雾水，觉得这都什么跟什么；当事人看了就会立刻回到那个房间、那张桌子、那顿饭、那个深夜，以及那个说完之后全场笑倒的瞬间。\n\n**01**\n\n![](articles/${dirName}/images/005.png)\n\n一凡：站得高，尿得远。\n\n孩儿们，吃橘子。\n\n吃火锅就吃火锅，可不许掀桌子。\n\n去摸摸唱。\n\n这些话单独看很抽象，但宿舍和朋友圈里的很多快乐，本来就不负责给外人解释。真正的笑点不是文字，而是说这句话的人、当时的语气和大家憋不住的表情。\n\n**02**\n\n![](articles/${dirName}/images/005.png)\n\n大飞哥：洗车店说小飞哥吐过的地方有打蜡效果。\n\n这句话的精髓在于，它把一件很狼狈的事情，硬生生说出了售后增值服务的感觉。人类文明能延续至今，靠的不只是科学技术，也靠大家把尴尬转化成段子的能力。\n\n**03**\n\n![](articles/${dirName}/images/005.png)\n\n思凡：好纠结，不想去阿里，怕他坑我。\n\n我可以周一二去亚马逊，周三去百度，其他时间去头条。\n\n国家安全中心可难进了，博士到那都是插U盘的。\n\n年轻时讨论工作，总有一种指点江山的气势。好像全世界公司都在等你翻牌子，今天亚马逊，明天百度，后天头条。后来才知道，选择工作这件事，大多数时候不是皇帝选妃，而是双向奔赴失败后的继续投递。\n\n**04**\n\n![](articles/${dirName}/images/005.png)\n\n荣荣：卡卡师兄，我上次在西安的酒吧看到一个歌手，长得特帅，唱歌好听。\n\n卡卡：荣荣，以后找对象可千万别太花痴啊。\n\n荣荣：我 C 语言都快忘光了，就记得一个 cin，cout。\n\n这就是学生时代的真实状态：一边担心对象，一边担心 C 语言；一边觉得自己要搞学术搞事业，一边脑子里只剩 cin 和 cout。知识会遗忘，八卦不会。\n\n**05**\n\n![](articles/${dirName}/images/005.png)\n\n小飞哥（喝醉）：思凡，给你介绍我小姨子，我小姨子特靠谱。思凡真的，你如果看上了，你努力一下！\n\n排版：王荣荣\n\n责编：张思凡\n\n很多年后，这些话未必还好笑。但它们保存了一种状态：大家还聚在一起，还能互相乱开玩笑，还没有被工作、城市、家庭和人生规划彻底打散。所谓趣言趣闻，趣只是表面，真正珍贵的是闻。有人说过，有人听见，有人记了下来。`],
  ['散篇-10-读研读废了是什么体验', () => `读研读废了是什么体验？\n\n深刻理解博硕士的毕业要求与毕业难度。知道“快了”不一定是快了，“问题不大”通常问题很大，“你再改改”约等于人生进入下一轮循环。\n\n熟练使用微信、微博、QQ、支付宝、淘宝、京东、高德地图等各大 APP。科研不一定顺利，生活技能一定全面。能在三分钟内找到优惠券，五分钟内判断哪家外卖满减最优，十分钟内从学校任意位置规划出一条避开导师的路线。\n\n熟练购物、退换货、抢优惠券等流程。尤其擅长在贫穷和体面之间寻找平衡：东西可以买便宜的，但快递备注一定要写清楚。\n\n熟练论文查找、编纂、相关软件使用等。包括但不限于：下载论文、管理论文、打开论文、关闭论文、假装读过论文，以及在组会上用三页 PPT 证明自己这周确实和论文发生过关系。\n\n在刺激战场、王者荣耀等竞技类活动中取得不错的名次。毕竟科研受挫之后，人总要在别的地方找回一点控制感。现实里做不出实验，峡谷里至少还能推塔。\n\n打字与思维切换速度飞快，能同时以不同身份在微博、微信、豆瓣等社交产品上发表言论。上午是严谨科研工作者，下午是职场观察家，晚上是情感博主，凌晨是“我到底为什么读研”受害者。\n\n熟练多显示器配置、多接口转换，在书桌布置方面颇有心得。桌面越专业，内心越慌张。一个屏幕放论文，一个屏幕放代码，一个屏幕放视频。导师推门进来之前，一切都可以解释为交叉验证。\n\n熟悉开会流程，分为四个阶段：开会、挨训、与上次会议内容对比、散会。\n\n熟悉开会采购水果的流程，以及散会回收水果的步骤。水果是学术会议里少有的确定性。课题不一定推进，香蕉总会变少。\n\n熟悉法律中对自己有利的一部分。如《中华人民共和国劳动法》第三条指出，劳动者具有取得劳动报酬的权利。虽然研究生是不是劳动者这个问题仍需进一步研究，但先熟悉起来总没有坏处。\n\n熟悉马克思哲学的本质思想，熟知客观存在不会以人的意志为转移。比如论文不会因为你不想写就自动完成，导师也不会因为你不看手机就停止发消息。\n\n了解社会主义的优越性，及社会主义终将并且必然代替资本主义。也了解食堂二楼比一楼贵，校外黄焖鸡比食堂更能安慰人。\n\n了解各大公司招聘流程、招聘需求及应聘难度。读研前以为自己是未来科研工作者，读研后发现自己是秋招预备役、考公观察员、互联网边缘人和论文延期风险综合体。\n\n最后，读研读废并不代表毫无收获。只是收获的东西和入学时想象的不太一样。你可能没有成为学术明星，但你会成为一个熟练检索、熟练忍耐、熟练自嘲、熟练在深夜重启人生计划的人。\n\n某种意义上，也算复合型人才。`],
  ['散篇-11-男朋友不回消息怎么办', () => `男朋友不回消息怎么办？\n\n首先不要慌，系统无响应不一定代表服务已下线，也可能只是消息队列发生了堵塞。建议及时 request 一下他身边的老板、哥们、红颜知己，看看是谁在那里一天到晚老发消息，把队列堵上了。\n\n如果 request 无响应，可以尝试轮询 CPU 占用情况。常见高占用任务包括游戏、Paper、短视频、酒局、加班，以及“我就躺一会儿结果睡到第二天”。如果确认 CPU 被游戏或 Paper 等大规模计算资源占用，可以考虑 kill 掉。\n\n至于 kill 哪个，这个需要根据实际业务场景谨慎判断。\n\n如果 CPU 正常、网络正常、服务也正常，但就是不回，那可能是你的消息优先级被系统调低了。建议提高自己的线程优先级，例如发送“你忙吧”，这四个字通常具有较强中断能力。比它更强的是“我没事”，属于危险指令，不建议频繁使用，容易造成系统恐慌。\n\n还有一种情况，是对方开启了节能模式。表现为：朋友圈能刷新，游戏能在线，群聊能发言，唯独你的聊天框长期静默。这种问题不属于技术故障，属于产品设计缺陷。\n\n如果多次重试仍无响应，可以进行版本评估。旧版本男朋友可能存在消息延迟、情绪缓存过大、沟通接口不稳定等问题。此时有两种方案：一是要求对方升级补丁，明确响应时间和异常处理机制；二是更换一个性能更加强劲、接口文档更清晰、售后服务更稳定的男朋友。\n\n当然，感情系统最麻烦的地方在于，它没有统一文档，也没有稳定接口。真要长期无响应，建议及时止损。毕竟青春不是后台服务，不能一直挂起等待。`],
]);

function buildDraft({ dirName, meta, cleanBody }) {
  const title = titleWithoutPrefix(dirName, meta.title);
  if (customBodies.has(dirName)) return customBodies.get(dirName)({ dirName, meta, cleanBody });
  const body = rebaseImages(cleanBody, dirName).replace(/\n{3,}/g, '\n\n').trim();
  const closing = generateClosing(dirName, title);
  return closing ? `${body}\n\n${closing}` : body;
}

function buildNotes({ dirName, meta, score, reviewName, reviewText }) {
  const title = titleWithoutPrefix(dirName, meta.title);
  const verdict = sectionAfter(reviewText, ['复评结论', '总体印象']) || plainExcerpt(reviewText, 360);
  const advice = sectionAfter(reviewText, ['可再打磨', '写作建议', '改进建议']) || '保留作者原有语气，继续收紧结构，强化结尾落点。';
  return `# 修改说明：${title}\n\n## 当前依据\n\n- 原文：\`articles/${dirName}/index.md\`\n- 参考评价：\`${reviewName || '无'}\`\n- 当前评分：${score ? `${score}/10` : '未记录'}\n- 目标评分：10/10\n\n## 本轮改稿策略\n\n这是第一版 AI 改稿，优先做到“有完整可读稿”，而不是一次性重写成终稿。长篇尽量保留作者原声和原始材料，主要处理结构、过渡、结尾；短篇和低分文章适当扩写，让它们从段子或素材变成完整文章。\n\n## 评价摘录\n\n${verdict || '暂无评价摘录。'}\n\n## 可继续打磨\n\n${advice}\n\n## 下一轮建议\n\n1. 人工逐段读一遍，删掉不像作者会说的话。\n2. 对关键人物首次出现补身份标签，降低非熟人读者门槛。\n3. 检查结尾是否落在具体物件、动作或作者式玩笑上。\n4. 如果要收入成书，再按卷目统一口径和时间线。\n`;
}

async function main() {
  const ranking = existsSync(join(ROOT, 'website', 'ranking.md'))
    ? await readFile(join(ROOT, 'website', 'ranking.md'), 'utf8')
    : '';
  const dirs = (await readdir(ARTICLES_DIR, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));

  let created = 0;
  let refreshed = 0;
  let skipped = 0;
  for (const dirName of dirs) {
    const sourcePath = join(ARTICLES_DIR, dirName, 'index.md');
    if (!existsSync(sourcePath)) continue;
    const outDir = join(AI_DIR, groupOf(dirName), dirName);
    const outIndex = join(outDir, 'index.md');
    const outNotes = join(outDir, 'notes.md');
    const existed = existsSync(outIndex);
    if (!FORCE && existsSync(outIndex)) {
      const existing = await readFile(outIndex, 'utf8');
      if (!REFRESH_GENERATED || !isGeneratedDraft(existing)) {
        skipped += 1;
        continue;
      }
    }

    const content = await readFile(sourcePath, 'utf8');
    const meta = parseFrontmatter(content);
    const title = titleWithoutPrefix(dirName, meta.title);
    const cleanBody = stripBoilerplate(content);
    const articleFiles = (await readdir(join(ARTICLES_DIR, dirName), { withFileTypes: true })).filter((entry) => entry.isFile()).map((entry) => entry.name);
    const reviewName = latestReviewName(articleFiles);
    const reviewText = reviewName ? await readFile(join(ARTICLES_DIR, dirName, reviewName), 'utf8') : '';
    const score = parseScore(ranking, dirName);
    const draftBody = buildDraft({ dirName, meta, cleanBody });
    const index = [
      '---',
      `title: ${yamlQuote(title)}`,
      `author: ${yamlQuote(meta.author || '凡复思忖')}`,
      `source_article: ${yamlQuote(`../../../articles/${dirName}/index.md`)}`,
      'target_score: "10/10"',
      'status: "AI 修改稿"',
      'edit_round: "v1"',
      `edited: ${yamlQuote(TODAY)}`,
      '---',
      '',
      `# ${title}`,
      '',
      draftBody,
      '',
      '---',
      '',
      `*原文: [${title}](#/articles/${encodeURI(dirName)}/index.md)*`,
      '',
    ].join('\n');

    await mkdir(outDir, { recursive: true });
    await writeFile(outIndex, index, 'utf8');
    await writeFile(outNotes, buildNotes({ dirName, meta, score, reviewName, reviewText }), 'utf8');
    if (existed) refreshed += 1;
    else created += 1;
  }
  console.log(`created ${created}, refreshed ${refreshed}, skipped ${skipped}`);
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
