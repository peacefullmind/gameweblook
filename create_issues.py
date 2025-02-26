import os
import glob
from datetime import datetime, timedelta
from github import Github

def create_issue_for_log(gh, repo_name, log_file):
    """为日志文件创建GitHub Issue"""
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析日志内容
        lines = content.split('\n')
        website_name = lines[0].split(': ')[1]
        detect_time = lines[1].split(': ')[1]
        urls_count = lines[2].split(': ')[1]
        
        # 创建Issue标题和内容
        title = f"[{website_name}] 发现{urls_count}个新增页面 - {detect_time}"
        body = f"### 检测时间\n{detect_time}\n\n### 新增页面\n"
        
        # 添加URL列表
        for line in lines[4:]:  # 跳过头部信息，只包含URL
            if line.strip():
                body += f"- {line}\n"
        
        # 获取仓库并创建Issue
        repo = gh.get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body, labels=['新增页面'])
        print(f"已为 {website_name} 创建Issue: {issue.html_url}")
        
    except Exception as e:
        print(f"创建Issue失败: {str(e)}")

def main():
    # 获取GitHub Token
    github_token = os.environ.get('LOG_TOKEN')
    if not github_token:
        print("错误: 未设置LOG_TOKEN环境变量")
        return
    
    # 获取仓库名称
    github_repository = os.environ.get('GITHUB_REPOSITORY')
    if not github_repository:
        print("错误: 未设置GITHUB_REPOSITORY环境变量")
        return
    
    # 初始化GitHub API客户端
    gh = Github(github_token)
    
    # 获取最近1分钟内创建的日志文件
    current_time = datetime.now()
    log_dir = 'logs'
    
    for log_file in glob.glob(os.path.join(log_dir, '*.txt')):
        # 跳过汇总文件
        if log_file.startswith('summary_'):
            continue
        
        # 获取文件修改时间
        file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        
        # 只处理最近1分钟内创建的文件
        if (current_time - file_time).total_seconds() <= 60:
            create_issue_for_log(gh, github_repository, log_file)

if __name__ == '__main__':
    main()