import os
import yaml
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import feedparser

def load_config():
    """加载配置文件"""
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def download_sitemap(url, save_path):
    """下载网站地图"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        return True
    except Exception as e:
        print(f"下载失败: {url}\n错误信息: {str(e)}")
        return False

def download_rss(url, save_path):
    """下载RSS源"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        return True
    except Exception as e:
        print(f"下载RSS失败: {url}\n错误信息: {str(e)}")
        return False

def parse_sitemap(file_path):
    """解析网站地图，返回URL集合"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        # 处理不同的命名空间
        ns = {'ns': root.tag.split('}')[0].strip('{')}
        urls = set()
        for url in root.findall('.//ns:url/ns:loc', ns):
            urls.add(url.text)
        return urls
    except Exception as e:
        print(f"解析失败: {file_path}\n错误信息: {str(e)}")
        return set()

def parse_rss(file_path):
    """解析RSS源，返回URL集合"""
    try:
        feed = feedparser.parse(file_path)
        urls = set()
        for entry in feed.entries:
            urls.add(entry.link)
        return urls
    except Exception as e:
        print(f"解析RSS失败: {file_path}\n错误信息: {str(e)}")
        return set()

def compare_urls(old_urls, new_urls):
    """比较新旧URL集合，返回新增的URL"""
    return new_urls - old_urls

def save_new_urls(website_name, new_urls, log_dir):
    """保存新增的URL到日志文件"""
    if not new_urls:
        return
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_path = os.path.join(log_dir, f"{website_name}_{timestamp}.txt")
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"网站: {website_name}\n")
        f.write(f"检测时间: {timestamp}\n")
        f.write(f"新增页面数量: {len(new_urls)}\n\n")
        for url in sorted(new_urls):
            f.write(f"{url}\n")

def process_sitemap(website, sitemap_dir, log_dir):
    """处理网站地图"""
    name = website['name']
    sitemap_url = website['sitemap']
    print(f"处理网站地图: {name}")
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    new_sitemap_path = sitemap_dir / f"{name}_{timestamp}.xml"
    
    if not download_sitemap(sitemap_url, new_sitemap_path):
        return
    
    new_urls = parse_sitemap(new_sitemap_path)
    if not new_urls:
        return
    
    old_files = sorted(
        [f for f in sitemap_dir.glob(f"{name}_*.xml") if f != new_sitemap_path],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if old_files:
        old_urls = parse_sitemap(old_files[0])
        added_urls = compare_urls(old_urls, new_urls)
        if added_urls:
            save_new_urls(name, added_urls, log_dir)
            print(f"发现 {len(added_urls)} 个新增页面，已保存到日志文件")
        else:
            print("未发现新增页面")
    else:
        save_new_urls(name, new_urls, log_dir)
        print(f"首次运行，保存了 {len(new_urls)} 个页面")

def process_rss(website, rss_dir, log_dir):
    """处理RSS源"""
    name = website['name']
    rss_url = website['rss']
    print(f"处理RSS源: {name}")
    
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    new_rss_path = rss_dir / f"{name}_{timestamp}.xml"
    
    if not download_rss(rss_url, new_rss_path):
        return
    
    new_urls = parse_rss(new_rss_path)
    if not new_urls:
        return
    
    old_files = sorted(
        [f for f in rss_dir.glob(f"{name}_*.xml") if f != new_rss_path],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if old_files:
        old_urls = parse_rss(old_files[0])
        added_urls = compare_urls(old_urls, new_urls)
        if added_urls:
            save_new_urls(name, added_urls, log_dir)
            print(f"发现 {len(added_urls)} 个新增页面，已保存到日志文件")
        else:
            print("未发现新增页面")
    else:
        save_new_urls(name, new_urls, log_dir)
        print(f"首次运行，保存了 {len(new_urls)} 个页面")

def merge_logs(log_dir):
    """合并本次运行新生成的日志文件到一个汇总文件中"""
    # 获取当前时间作为基准时间
    current_time = datetime.now()
    
    # 获取所有日志文件，只选择最近1分钟内创建的文件（本次运行生成的）
    log_files = []
    for file in Path(log_dir).glob('*.txt'):
        # 跳过之前的汇总文件
        if file.name.startswith('summary_'):
            continue
        # 获取文件的创建时间
        file_time = datetime.fromtimestamp(file.stat().st_mtime)
        # 如果文件是最近1分钟内创建的，则添加到列表中
        if (current_time - file_time).total_seconds() <= 60:
            log_files.append(file)
    
    if not log_files:
        print("本次运行没有新增日志文件，无需汇总")
        return

    # 创建汇总文件
    timestamp = current_time.strftime('%Y-%m-%d_%H-%M-%S')
    summary_path = os.path.join(log_dir, f"summary_{timestamp}.txt")
    
    with open(summary_path, 'w', encoding='utf-8') as summary_file:
        summary_file.write(f"汇总时间: {timestamp}\n")
        summary_file.write(f"本次新增日志文件数: {len(log_files)}\n\n")
        
        # 按网站名称分组处理日志
        website_logs = {}
        for log_file in log_files:
            # 从文件名中提取网站名称
            website_name = log_file.stem.split('_')[0]
            
            if website_name not in website_logs:
                website_logs[website_name] = []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                website_logs[website_name].append({
                    'time': log_file.stem.split('_', 1)[1],
                    'content': content
                })
        
        # 按网站名称输出汇总内容
        for website_name, logs in sorted(website_logs.items()):
            summary_file.write(f"=== {website_name} ===\n\n")
            # 按时间顺序输出每个日志
            for log in sorted(logs, key=lambda x: x['time']):
                summary_file.write(f"--- {log['time']} ---\n")
                summary_file.write(log['content'])
                summary_file.write("\n")
            summary_file.write("\n")
    
    print(f"已生成本次新增日志的汇总文件: {summary_path}")

def main():
    # 加载配置
    config = load_config()
    
    # 创建必要的目录
    sitemap_dir = Path(config['storage']['sitemap_dir'])
    log_dir = Path(config['storage']['log_dir'])
    rss_dir = Path(config['storage']['rss_dir'])
    
    for directory in [sitemap_dir, log_dir, rss_dir]:
        directory.mkdir(exist_ok=True)
    
    # 处理每个网站
    for website in config['websites']:
        print(f"\n处理网站: {website['name']}")
        if 'sitemap' in website:
            process_sitemap(website, sitemap_dir, log_dir)
        elif 'rss' in website:
            process_rss(website, rss_dir, log_dir)
    
    # 合并所有日志文件
    merge_logs(log_dir)
    print("\n已生成日志汇总文件")

if __name__ == '__main__':
    main()