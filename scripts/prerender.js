const fs = require('fs');
const path = require('path');

const marked = require('marked');

const BASE_DIR = path.join(__dirname, '..');

function readFile(filePath) {
  try {
    return fs.readFileSync(path.join(BASE_DIR, filePath), 'utf-8');
  } catch (error) {
    console.error(`读取文件失败: ${filePath}`, error.message);
    return null;
  }
}

function writeFile(filePath, content) {
  try {
    fs.writeFileSync(path.join(BASE_DIR, filePath), content, 'utf-8');
    console.log(`文件写入成功: ${filePath}`);
  } catch (error) {
    console.error(`写入文件失败: ${filePath}`, error.message);
  }
}

function generateMarkdownContent(title, markdown) {
  if (!markdown) {
    return `<h2>${title}</h2><p>暂无数据，请稍后刷新页面。</p>`;
  }
  
  let html = marked.parse(markdown);
  
  return `<div class="report-section">
    <h2 style="color: var(--primary-color); border-bottom: 2px solid var(--primary-color); padding-bottom: 10px; margin-bottom: 30px;">${title}</h2>
    <div class="markdown-content">${html}</div>
  </div>`;
}

function generateCoreInsights(jsonData) {
  if (!jsonData) {
    return '<ul><li><strong>市场情绪:</strong> 正在分析市场数据...</li><li><strong>投资建议:</strong> 基于最新市场动态提供策略参考</li><li><strong>风险提示:</strong> 请关注市场波动风险</li></ul>';
  }
  
  try {
    const data = JSON.parse(jsonData);
    if (data.insights && Array.isArray(data.insights)) {
      let html = '<ul>';
      data.insights.forEach(([category, insight]) => {
        html += `<li><strong>${category}:</strong> ${insight}</li>`;
      });
      html += '</ul>';
      return html;
    }
  } catch (error) {
    console.error('解析JSON数据失败:', error.message);
  }
  
  return '<ul><li><strong>市场情绪:</strong> 正在分析市场数据...</li><li><strong>投资建议:</strong> 基于最新市场动态提供策略参考</li><li><strong>风险提示:</strong> 请关注市场波动风险</li></ul>';
}

function extractInterpretationsFromJSON(jsonData) {
  if (!jsonData) return {};
  
  try {
    const data = JSON.parse(jsonData);
    return data.interpretations || {};
  } catch (error) {
    console.error('解析JSON数据失败:', error.message);
    return {};
  }
}

function replaceSection(html, sectionName, content) {
  const startMarker = `<!-- PRERENDER:${sectionName}:START -->`;
  const endMarker = `<!-- PRERENDER:${sectionName}:END -->`;
  
  const startIndex = html.indexOf(startMarker);
  const endIndex = html.indexOf(endMarker);
  
  if (startIndex === -1 || endIndex === -1) {
    console.warn(`未找到标记: ${sectionName}`);
    return html;
  }
  
  return html.substring(0, startIndex + startMarker.length) + '\n' + content + '\n' + html.substring(endIndex);
}

async function main() {
  console.log('开始预渲染页面...');
  
  const indexHtml = readFile('index.html');
  if (!indexHtml) {
    console.error('无法读取index.html');
    process.exit(1);
  }
  
  const todayReport = readFile('today_report.md');
  const fiveDayReport = readFile('5day_report.md');
  const marketReport = readFile('output/市场分析结果.json');
  
  const todayHtml = generateMarkdownContent('📅 今日报告', todayReport);
  const fiveDayHtml = generateMarkdownContent('📊 5天报告', fiveDayReport);
  
  const coreInsightsHtml = generateCoreInsights(marketReport);
  const interpretations = extractInterpretationsFromJSON(marketReport);
  
  let finalHtml = indexHtml;
  
  const combinedReportContent = `${todayHtml}<hr style="margin: 50px 0; border: none; height: 2px; background-color: var(--border-color);">${fiveDayHtml}`;
  finalHtml = replaceSection(finalHtml, 'README', combinedReportContent);
  
  finalHtml = replaceSection(finalHtml, 'CORE_INSIGHTS', coreInsightsHtml);
  
  if (interpretations.riskEnvironment) {
    finalHtml = replaceSection(finalHtml, 'RISK_ENVIRONMENT', `<pre style="background-color: var(--code-bg); padding: 10px; border-radius: 6px; font-size: 0.9rem;">${interpretations.riskEnvironment}</pre>`);
  }
  
  if (interpretations.marketStructure) {
    finalHtml = replaceSection(finalHtml, 'MARKET_STRUCTURE', `<pre style="background-color: var(--code-bg); padding: 10px; border-radius: 6px; font-size: 0.9rem;">${interpretations.marketStructure}</pre>`);
  }
  
  if (interpretations.sectorRotation) {
    finalHtml = replaceSection(finalHtml, 'SECTOR_ROTATION', `<pre style="background-color: var(--code-bg); padding: 10px; border-radius: 6px; font-size: 0.9rem;">${interpretations.sectorRotation}</pre>`);
  }
  
  if (interpretations.chinaUsLinkage) {
    finalHtml = replaceSection(finalHtml, 'CHINA_US_LINKAGE', `<pre style="background-color: var(--code-bg); padding: 10px; border-radius: 6px; font-size: 0.9rem;">${interpretations.chinaUsLinkage}</pre>`);
  }
  
  if (interpretations.guzhai) {
    finalHtml = replaceSection(finalHtml, 'GUZHAI', `<pre style="background-color: var(--code-bg); padding: 10px; border-radius: 6px; font-size: 0.9rem;">${interpretations.guzhai}</pre>`);
  }
  
  if (interpretations.liudongxing) {
    finalHtml = replaceSection(finalHtml, 'LIUDONGXING', `<pre style="background-color: var(--code-bg); padding: 10px; border-radius: 6px; font-size: 0.9rem;">${interpretations.liudongxing}</pre>`);
  }
  
  if (interpretations.oil) {
    finalHtml = replaceSection(finalHtml, 'OIL', `<pre style="background-color: var(--code-bg); padding: 10px; border-radius: 6px; font-size: 0.9rem;">${interpretations.oil}</pre>`);
  }
  
  writeFile('index.html', finalHtml);
  
  console.log('预渲染完成！');
}

main().catch(console.error);