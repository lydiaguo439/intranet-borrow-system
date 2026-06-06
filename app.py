"""
文件借阅管理系统 - Web应用主程序
完全离线运行，数据本地存储
"""

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
from io import BytesIO

app = Flask(__name__)

# ===== 配置 =====
# 网络配置
INTERNAL_IP = 'xxx.xxx.xxx.xxx'  # 改成你的内网IP地址（例如：192.168.1.50）

# 这些路径在工作电脑上需要修改
BASE_DIR = Path(__file__).parent
BORROW_DB_PATH = BASE_DIR / "借阅台账.xlsx"
RECEIVE_DB_PATH = Path("D:/收文归档/收文台账.xlsx")  # 需要修改为实际路径

print(f"[系统信息] 项目目录: {BASE_DIR}")
print(f"[系统信息] 借阅台账路径: {BORROW_DB_PATH}")
print(f"[系统信息] 收文台账路径: {RECEIVE_DB_PATH}")

# ===== 初始化 =====
def init_borrow_db():
    """初始化借阅台账"""
    if not BORROW_DB_PATH.exists():
        df = pd.DataFrame(columns=[
            '序号', '借阅时间', '文件序号', '文件名', '来文单位',
            '借阅人', '借阅类型', '借阅天数', '应还时间', '用途',
            '归还时间', '状态', '备注'
        ])
        df.to_excel(BORROW_DB_PATH, index=False, sheet_name='借阅记录')

def load_receive_files():
    """从收文台账加载文件列表"""
    try:
        df = pd.read_excel(RECEIVE_DB_PATH)
        return df.to_dict('records')
    except Exception as e:
        print(f"读取收文台账错误: {e}")
        return []

def load_borrow_records():
    """加载借阅台账"""
    try:
        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录')
        return df.to_dict('records')
    except Exception as e:
        print(f"读取借阅台账错误: {e}")
        return []

def save_borrow_record(data):
    """保存借阅记录到台账"""
    try:
        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录')
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(BORROW_DB_PATH, index=False, sheet_name='借阅记录')
        return True
    except Exception as e:
        print(f"保存记录错误: {e}")
        return False

def update_borrow_record(record_id, updates):
    """更新借阅记录"""
    try:
        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录', dtype=str)
        for col, val in updates.items():
            df.at[record_id, col] = str(val)
        df.to_excel(BORROW_DB_PATH, index=False, sheet_name='借阅记录')
        return True
    except Exception as e:
        print(f"更新记录错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_matching_records(date, unit, borrower=None, filename=None):
    """根据日期、单位和可选的借阅人、文件名查找匹配的借阅记录"""
    try:
        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录')
        matches = df[(df['来文日期'] == date) & (df['来文单位'] == unit) & (df['状态'] == '借出')]

        # 如果有借阅人信息，进一步过滤
        if borrower:
            matches = matches[matches['借阅人'] == borrower]

        # 如果有文件名信息，进一步过滤
        if filename:
            matches = matches[matches['文件名'] == filename]

        return matches.to_dict('records')
    except Exception as e:
        print(f"查询错误: {e}")
        return []

# ===== API 路由 =====

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def get_files():
    """获取收文列表 - 已废弃（手填模式）"""
    return jsonify([])

@app.route('/api/borrow', methods=['POST'])
def borrow_file():
    """录入借阅 - 手填模式"""
    data = request.json

    try:
        # 验证必填字段
        required_fields = ['date', 'unit', 'borrower', 'type', 'days']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'缺少必填项: {field}'}), 400

        # 计算应还时间
        borrow_days = int(data.get('days', 1))
        borrow_time = datetime.now()
        due_time = borrow_time + timedelta(days=borrow_days)

        record = {
            '来文日期': data.get('date'),
            '来文单位': data.get('unit'),
            '文件名': data.get('filename', ''),
            '文号': data.get('docnum', ''),
            '借阅时间': borrow_time.strftime('%Y-%m-%d %H:%M'),
            '借阅人': data.get('borrower'),
            '借阅类型': data.get('type'),  # 纸质/电子
            '借阅天数': borrow_days,
            '应还时间': due_time.strftime('%Y-%m-%d %H:%M'),
            '用途': data.get('purpose', ''),
            '归还时间': '',
            '状态': '借出',
            '备注': ''
        }

        if save_borrow_record(record):
            return jsonify({'success': True, 'message': '借阅记录已保存'})
        else:
            return jsonify({'success': False, 'message': '保存失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/unreturned', methods=['GET'])
def get_admin_unreturned():
    """获取所有待归还的文件（管理员用）"""
    try:
        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录')
        unreturned = df[df['状态'] == '借出']

        # 转换为dict并处理NaN值
        records = []
        for _, row in unreturned.iterrows():
            record = {}
            for col in row.index:
                val = row[col]
                if pd.isna(val):
                    record[col] = ''
                else:
                    record[col] = str(val)
            records.append(record)

        return jsonify({'success': True, 'records': records})
    except Exception as e:
        print(f"查询错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/export', methods=['GET'])
def export_unreturned():
    """导出待归还文件清单为Excel"""
    try:
        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录', dtype=str)
        unreturned = df[df['状态'] == '借出'].copy()

        if len(unreturned) == 0:
            unreturned = pd.DataFrame(columns=df.columns)

        # 转换为内存中的Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            unreturned.to_excel(writer, sheet_name='待归还清单', index=False)

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'待归还文件清单_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    except Exception as e:
        print(f"导出错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/my-borrows', methods=['GET'])
def query_my_borrows():
    """获取某个借阅人的所有借阅记录"""
    name = request.args.get('name', '').strip()

    if not name:
        return jsonify({'success': False, 'message': '需要提供名字'}), 400

    try:
        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录')
        my_records = df[(df['借阅人'] == name) & (df['状态'] == '借出')]

        # 转换为dict并处理NaN值
        records = []
        for _, row in my_records.iterrows():
            record = {}
            for col in row.index:
                val = row[col]
                if pd.isna(val):
                    record[col] = ''
                else:
                    record[col] = str(val)
            records.append(record)

        return jsonify({'success': True, 'records': records})
    except Exception as e:
        print(f"查询错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/transfer', methods=['POST'])
def transfer_borrow():
    """将文件转交给另一个人"""
    data = request.json
    date = data.get('date')
    unit = data.get('unit')
    to_name = data.get('to_name', '').strip()
    days = data.get('days', 1)

    if not date or not unit or not to_name:
        return jsonify({'success': False, 'message': '缺少必填信息'}), 400

    try:
        # 对天数进行四舍五入，最少1天
        days = max(1, round(float(days)))

        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录', dtype=str)
        mask = (df['来文日期'] == date) & (df['来文单位'] == unit) & (df['状态'] == '借出')

        if not mask.any():
            return jsonify({'success': False, 'message': '未找到该文件的借出记录'}), 404

        # 更新借阅人和应还时间
        idx = df[mask].index[0]
        df.at[idx, '借阅人'] = to_name

        # 重新计算应还时间
        now = datetime.now()
        new_due_time = now + timedelta(days=days)
        df.at[idx, '应还时间'] = new_due_time.strftime('%Y-%m-%d %H:%M')

        df.to_excel(BORROW_DB_PATH, index=False, sheet_name='借阅记录')

        return jsonify({'success': True, 'message': '转交成功'})
    except Exception as e:
        print(f"转交错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/unreturned', methods=['GET'])
def get_unreturned_files():
    """获取未归还的文件列表 - 支持按单位、文件名、借阅人搜索"""
    mode = request.args.get('mode', 'unit').strip()
    query = request.args.get('query', '').strip()

    if not query:
        return jsonify({'success': False, 'message': '搜索条件不能为空'}), 400

    try:
        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录')
        unreturned = df[df['状态'] == '借出']

        # 根据搜索模式过滤
        if mode == 'unit':
            # 按单位精确匹配
            results = unreturned[unreturned['来文单位'] == query]
        elif mode == 'filename':
            # 按文件名模糊匹配
            results = unreturned[unreturned['文件名'].str.contains(query, na=False, case=False)]
        elif mode == 'borrower':
            # 按借阅人精确匹配
            results = unreturned[unreturned['借阅人'] == query]
        else:
            return jsonify({'success': False, 'message': '不支持的搜索模式'}), 400

        # 转换为dict并处理NaN值
        records = []
        for _, row in results.iterrows():
            record = {}
            for col in row.index:
                val = row[col]
                if pd.isna(val):
                    record[col] = ''
                else:
                    record[col] = str(val)
            records.append(record)

        return jsonify({'success': True, 'records': records})
    except Exception as e:
        print(f"查询错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/return', methods=['POST'])
def return_file():
    """归还文件 - 根据日期和单位匹配，多条时返回第一条"""
    data = request.json
    date = data.get('date')
    unit = data.get('unit')

    try:
        if not date or not unit:
            return jsonify({'success': False, 'message': '需要提供来文日期和单位'}), 400

        df = pd.read_excel(BORROW_DB_PATH, sheet_name='借阅记录')
        mask = (df['来文日期'] == date) & (df['来文单位'] == unit) & (df['状态'] == '借出')

        if not mask.any():
            return jsonify({'success': False, 'message': '找不到该文件的借出记录'}), 404

        # 更新第一条匹配记录
        record_index = df[mask].index[0]

        updates = {
            '状态': '已归还',
            '归还时间': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        if update_borrow_record(record_index, updates):
            return jsonify({'success': True, 'message': '归还成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'}), 500
    except Exception as e:
        print(f"归还错误: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/records', methods=['GET'])
def get_records():
    """获取借阅记录"""
    records = load_borrow_records()

    # 标记逾期
    now = datetime.now()
    for record in records:
        if record['状态'] == '借出':
            try:
                due_time = datetime.strptime(record['应还时间'], '%Y-%m-%d %H:%M')
                if now > due_time:
                    record['is_overdue'] = True
                else:
                    record['is_overdue'] = False
            except:
                record['is_overdue'] = False
        else:
            record['is_overdue'] = False

    return jsonify(records)

@app.route('/api/overdue', methods=['GET'])
def get_overdue():
    """获取逾期记录"""
    records = load_borrow_records()
    now = datetime.now()

    overdue = []
    for i, record in enumerate(records):
        if record['状态'] == '借出':
            try:
                due_time = datetime.strptime(record['应还时间'], '%Y-%m-%d %H:%M')
                if now > due_time:
                    record['days_overdue'] = (now - due_time).days
                    overdue.append(record)
            except:
                pass

    return jsonify(overdue)

# ===== 启动 =====
if __name__ == '__main__':
    try:
        print("\n[启动中] 初始化借阅台账...")
        init_borrow_db()
        print("[✓] 借阅台账已初始化")

        print("[启动中] 加载收文文件列表...")
        files = load_receive_files()
        print(f"[✓] 已加载 {len(files)} 份文件")

        print("\n" + "="*50)
        print("✓ 系统启动成功！")
        print("="*50)
        print("\n请打开浏览器访问:")
        print("  http://localhost:5000")
        print("\n或用手机扫描二维码")
        print("\n按 Ctrl+C 停止应用")
        print("="*50 + "\n")

        app.run(host=INTERNAL_IP, port=5000, debug=False)
    except Exception as e:
        print(f"\n[错误] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按任意键退出...")
        sys.exit(1)
