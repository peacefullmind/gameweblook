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

if __name__ == '__main__':
    main()