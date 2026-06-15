"""
TextNow Factory - 批量导入账号脚本
支持格式：CSV、TXT
必填字段：username, password, sid, token
可选字段：phone_number, email, proxy
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

import csv
import logging
from models.db import get_db
from config import BASE_DIR as CONFIG_BASE_DIR

log = logging.getLogger(__name__)


def import_from_csv(file_path):
    """
    从 CSV 文件导入账号
    :param file_path: CSV 文件路径
    :return: (success_count, failed_count, errors)
    """
    success = 0
    failed = 0
    errors = []
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    username = row.get('username', '').strip()
                    password = row.get('password', '').strip()
                    sid = row.get('sid', '').strip()
                    token = row.get('token', '').strip()
                    phone = row.get('phone_number', '').strip()
                    email = row.get('email', '').strip()
                    proxy = row.get('proxy', '').strip()
                    
                    if not username or not password:
                        errors.append(f"跳过：缺少用户名或密码 ({username})")
                        failed += 1
                        continue
                    
                    # 插入数据库
                    cur.execute(
                        """INSERT IGNORE INTO tn_accounts 
                           (username, password, sid, token, phone_number, email, proxy, status) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                        (username, password, sid, token, phone, email, proxy)
                    )
                    
                    if cur.rowcount > 0:
                        success += 1
                    else:
                        errors.append(f"跳过：账号已存在 ({username})")
                        failed += 1
                        
                except Exception as e:
                    errors.append(f"错误：{username} - {str(e)}")
                    failed += 1
            
            conn.commit()
            log.info(f"✅ CSV 导入完成：成功 {success} 条，失败 {failed} 条")
            
    except Exception as e:
        conn.rollback()
        log.error(f"❌ CSV 导入失败：{e}")
        raise
    finally:
        conn.close()
    
    return success, failed, errors


def import_from_txt(file_path):
    """
    从 TXT 文件导入账号（每行一个账号，格式：username:password:sid:token）
    :param file_path: TXT 文件路径
    :return: (success_count, failed_count, errors)
    """
    success = 0
    failed = 0
    errors = []
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                try:
                    # 支持多种分隔符
                    if ':' in line:
                        parts = line.split(':')
                    elif ',' in line:
                        parts = line.split(',')
                    else:
                        errors.append(f"第 {i} 行格式错误：{line[:30]}")
                        failed += 1
                        continue
                    
                    username = parts[0].strip()
                    password = parts[1].strip() if len(parts) > 1 else ''
                    sid = parts[2].strip() if len(parts) > 2 else ''
                    token = parts[3].strip() if len(parts) > 3 else ''
                    
                    if not username or not password:
                        errors.append(f"第 {i} 行缺少用户名或密码")
                        failed += 1
                        continue
                    
                    # 插入数据库
                    cur.execute(
                        """INSERT IGNORE INTO tn_accounts 
                           (username, password, sid, token, status) 
                           VALUES (?, ?, ?, ?, 1)""",
                        (username, password, sid, token)
                    )
                    
                    if cur.rowcount > 0:
                        success += 1
                    else:
                        errors.append(f"第 {i} 行：账号已存在 ({username})")
                        failed += 1
                        
                except Exception as e:
                    errors.append(f"第 {i} 行错误：{str(e)}")
                    failed += 1
            
            conn.commit()
            log.info(f"✅ TXT 导入完成：成功 {success} 条，失败 {failed} 条")
            
    except Exception as e:
        conn.rollback()
        log.error(f"❌ TXT 导入失败：{e}")
        raise
    finally:
        conn.close()
    
    return success, failed, errors


def main():
    """主函数：命令行交互"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量导入 TextNow 账号')
    parser.add_argument('--file', '-f', required=True, help='文件路径（CSV 或 TXT）')
    parser.add_argument('--format', '-fmt', choices=['csv', 'txt'], default='csv', help='文件格式')
    
    args = parser.parse_args()
    
    if args.format == 'csv':
        success, failed, errors = import_from_csv(args.file)
    else:
        success, failed, errors = import_from_txt(args.file)
    
    print(f"\n导入结果：")
    print(f"  成功：{success} 条")
    print(f"  失败：{failed} 条")
    
    if errors:
        print(f"\n错误信息（前 10 条）：")
        for err in errors[:10]:
            print(f"  - {err}")


if __name__ == '__main__':
    main()
