import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import pathlib
import plotly.graph_objects as go

class Excel3DVisualizer:
    def __init__(self):
        """初始化基于 tkinter 和 plotly 的 Excel 3D 可视化器。"""
        self.data_dict = {}
        self.global_point_map = {} # 名称映射坐标: name -> [x, y, z]
        self.merged_points = {}    # 层内合并好的点数据: layer_name -> DataFrame
        self.line_segments_dict = {} # 线段数据

    def run_gui(self):
        """
        供产品生成的代码中实例化的工具方法，调起 Tkinter 选择目录弹窗
        """
        root = tk.Tk()
        root.title("Excel 3D 可视化")
        root.geometry("400x150")

        self.status_label = tk.Label(root, text="请选择包含Excel文件的目录", pady=10)
        self.status_label.pack()

        # tkinter 选择目录按钮
        btn = tk.Button(root, text="选择目录", width=20, height=2, command=self._on_select_directory)
        btn.pack(pady=20)
        
        self.root = root
        # 居中显示窗口
        root.eval('tk::PlaceWindow . center')
        root.mainloop()

    def _on_select_directory(self):
        dir_path = filedialog.askdirectory(title="选择包含Excel文件的目录")
        if not dir_path:
            return
        
        self.status_label.config(text="正在加载解析，请稍候...")
        self.root.update()

        try:
            self.load_directory(dir_path)
            self.status_label.config(text=f"加载完成，已载入文件及表格关系")
            self.merge_data()
            self.status_label.config(text=f"合并完成，即将生成由于...")
            self.render_3d()
            messagebox.showinfo("成功", "3D 可视化已生成并在浏览器中打开")
        except Exception as e:
            messagebox.showerror("错误", repr(e))
            self.status_label.config(text="加载或渲染失败，请重试。")

    def load_directory(self, dir_path: str):
        """
        核心底层解析接口，允许无 GUI 情况下直接传入路径驱动数据处理
        """
        self.data_dict = {'default': {}}
        base_path = pathlib.Path(dir_path)
        
        # 扫描特定扩展名的 Excel 文件
        for file_path in base_path.glob("*"):
            if file_path.suffix not in ['.xlsx', '.xls']:
                continue
            if file_path.name.startswith('~'): # 跳过系统缓存Excel文件
                continue
            
            filename = file_path.stem
            try:
                # pandas 的 header=None 读取，配合 openpyxl
                df = pd.read_excel(file_path, engine='openpyxl', header=None)
            except Exception as e:
                print(f"Skipping {file_path.name} due to read error: {e}")
                continue
            
            # 按文件名是否带 + 识别分类
            if '+' in filename:
                layer_name, table_type = filename.split('+', 1)
                
                if layer_name not in self.data_dict:
                    self.data_dict[layer_name] = {}
                    
                # 散点级信息，从所有行列遍历
                if table_type in ['叠合名表', '叠合状态表']:
                    parsed_data = []
                    for row_idx, row in df.iterrows():
                        for col_idx, value in enumerate(row):
                            if pd.notna(value):
                                parsed_data.append({'row': row_idx, 'col': col_idx, 'data': value})
                    self.data_dict[layer_name][table_type] = pd.DataFrame(parsed_data)
                    
                # 坐标点信息，格式如 X:3000.0,Y:1500.0,Z:0 
                elif table_type == '叠合坐标表':
                    parsed_data = []
                    for row_idx, row in df.iterrows():
                        for col_idx, val in enumerate(row):
                            if pd.notna(val) and isinstance(val, str):
                                try:
                                    parts = val.split(',')
                                    coords = {}
                                    for p in parts:
                                        if ':' in p:
                                            k, v = p.split(':', 1)
                                            # 除以 100 缩小坐标尺寸
                                            coords[k.strip().lower()] = float(v.strip()) / 100.0
                                    parsed_data.append({
                                        'row': row_idx, 'col': col_idx,
                                        'x': coords.get('x', 0), 'y': coords.get('y', 0), 'z': coords.get('z', 0)
                                    })
                                except Exception:
                                    pass
                    self.data_dict[layer_name][table_type] = pd.DataFrame(parsed_data)
                    
                # 行级信息
                elif table_type == '平面线表':
                    parsed_data = []
                    for row_idx, row in df.iterrows():
                        # 三列至少
                        if len(row) >= 3 and pd.notna(row[0]) and pd.notna(row[1]) and pd.notna(row[2]):
                            parsed_data.append({'name': str(row[0]), 'start': str(row[1]), 'end': str(row[2])})
                    self.data_dict[layer_name][table_type] = pd.DataFrame(parsed_data)
                else:
                    self.data_dict['default'][filename] = df
            else:
                # 无加号的文件匹配
                if filename == '垂线表':
                    parsed_data = []
                    for row_idx, row in df.iterrows():
                        if len(row) >= 3 and pd.notna(row[0]) and pd.notna(row[1]) and pd.notna(row[2]):
                            parsed_data.append({'name': str(row[0]), 'start': str(row[1]), 'end': str(row[2])})
                    self.data_dict['垂线表'] = pd.DataFrame(parsed_data)
                else:
                    # 保留原样内容以供以后功能使用，无需可视化渲染干预
                    self.data_dict['default'][filename] = df
                    
    def merge_data(self):
        """
        内部状态合成，负责产出可视化阶段需要的关联数据结构。
        """
        self.global_point_map = {}
        self.merged_points = {}
        self.line_segments_dict = {}
        
        # 1. 散点归类与全局名称地址映射建立
        for layer_name, tables in self.data_dict.items():
            if layer_name in ['default', '垂线表']:
                continue
                
            if '叠合名表' in tables and '叠合状态表' in tables and '叠合坐标表' in tables:
                df_name = tables['叠合名表'].rename(columns={'data': 'name'})
                df_name['name'] = df_name['name'].astype(str)
                df_status = tables['叠合状态表'].rename(columns={'data': 'status'})
                df_coord = tables['叠合坐标表']
                
                # 先后基于行列序号将名表、状态表、坐标表横向联表查合
                merged = pd.merge(df_name, df_status, on=['row', 'col'], how='inner')
                merged = pd.merge(merged, df_coord, on=['row', 'col'], how='inner')
                
                self.merged_points[layer_name] = merged
                
                # 遍历充实全局点名册哈希查询结构
                for _, row in merged.iterrows():
                    self.global_point_map[row['name']] = {'x': row['x'], 'y': row['y'], 'z': row['z']}
                    
        # 2. 收集跨层或层级的“线段”：平面线表及垂线表
        # a. 平面线表层层抽取
        for layer_name, tables in self.data_dict.items():
            if layer_name in ['default', '垂线表']:
                continue
            if '平面线表' in tables:
                df_lines = tables['平面线表']
                for _, row in df_lines.iterrows():
                    start_name = row['start']
                    end_name = row['end']
                    if start_name in self.global_point_map and end_name in self.global_point_map:
                        self.line_segments_dict[row['name']] = {
                            'start': self.global_point_map[start_name],
                            'end': self.global_point_map[end_name]
                        }
        
        # b. 汇总提取通用垂线表
        if '垂线表' in self.data_dict and isinstance(self.data_dict['垂线表'], pd.DataFrame):
            df_lines = self.data_dict['垂线表']
            for _, row in df_lines.iterrows():
                start_name = row['start']
                end_name = row['end']
                if start_name in self.global_point_map and end_name in self.global_point_map:
                    self.line_segments_dict[row['name']] = {
                        'start': self.global_point_map[start_name],
                        'end': self.global_point_map[end_name]
                    }

    def render_3d(self):
        """
        依托 plotly 生成三维散点并拉起本地 HTML 工具，呈现矩阵形式的数据。
        """
        fig = go.Figure()
        
        for layer_name, df in self.merged_points.items():
            if df.empty:
                continue
                
            # 根据 realpoint/状态字段区分，非空且非零即为活动
            def is_active(val):
                sval = str(val).strip()
                return pd.notna(val) and sval != '' and sval != '0' and sval != '0.0'
            
            df['is_active'] = df['status'].apply(is_active)
            df_active = df[df['is_active'] == True]
            df_inactive = df[df['is_active'] == False]
            
            # 添加层的活动点组 (红色)
            if not df_active.empty:
                fig.add_trace(go.Scatter3d(
                    x=df_active['x'], y=df_active['y'], z=df_active['z'],
                    mode='markers+text',
                    marker=dict(size=6, color='red'),
                    text=df_active.apply(lambda row: f"{row['name']}<br>({row['row']},{row['col']})", axis=1),
                    textfont=dict(size=20),
                    textposition='top center',
                    name=f'{layer_name}-活动点'
                ))
            
            # 添加层的非活动点组 (灰色)
            if not df_inactive.empty:
                fig.add_trace(go.Scatter3d(
                    x=df_inactive['x'], y=df_inactive['y'], z=df_inactive['z'],
                    mode='markers+text',
                    marker=dict(size=6, color='gray'),
                    text=df_inactive.apply(lambda row: f"{row['name']}<br>({row['row']},{row['col']})", axis=1),
                    textfont=dict(size=20),
                    textposition='top center',
                    name=f'{layer_name}-非活动点'
                ))
                
            # 层内同行/同列间网格连线 (统一定义为灰色分离线条轨迹，宽幅为 1)
            ortho_x, ortho_y, ortho_z = [], [], []
            
            # 按行列归类分组进行首尾相邻串联
            for _, group in df.groupby('row'):
                group = group.sort_values(by='col')
                for i in range(len(group)-1):
                    p1 = group.iloc[i]
                    p2 = group.iloc[i+1]
                    ortho_x.extend([p1['x'], p2['x'], None])
                    ortho_y.extend([p1['y'], p2['y'], None])
                    ortho_z.extend([p1['z'], p2['z'], None])
                    
            for _, group in df.groupby('col'):
                group = group.sort_values(by='row')
                for i in range(len(group)-1):
                    p1 = group.iloc[i]
                    p2 = group.iloc[i+1]
                    ortho_x.extend([p1['x'], p2['x'], None])
                    ortho_y.extend([p1['y'], p2['y'], None])
                    ortho_z.extend([p1['z'], p2['z'], None])

            if ortho_x:
                fig.add_trace(go.Scatter3d(
                    x=ortho_x, y=ortho_y, z=ortho_z,
                    mode='lines',
                    line=dict(color='gray', width=1),
                    name=f'{layer_name}-正交网格线',
                    showlegend=False,
                    hoverinfo='none'
                ))

        # 业务线渲染（红显）
        line_x, line_y, line_z = [], [], []
        for name, pts in self.line_segments_dict.items():
            line_x.extend([pts['start']['x'], pts['end']['x'], None])
            line_y.extend([pts['start']['y'], pts['end']['y'], None])
            line_z.extend([pts['start']['z'], pts['end']['z'], None])
            
        if line_x:
            fig.add_trace(go.Scatter3d(
                x=line_x, y=line_y, z=line_z,
                mode='lines',
                line=dict(color='red', width=2),
                name='业务级关系连线',
                hoverinfo='none'
            ))

        # 主视口布局统属调整
        fig.update_layout(
            title="Excel数据3D可视化 - 点线矩阵",
            scene_camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
            scene=dict(aspectmode='data'),
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        # 将绘制产物输出并唤起浏览器开启
        output_path = pathlib.Path.cwd() / "output.html"
        fig.write_html(str(output_path), auto_open=True)

# 对于其他脚本或工具生成时的最简示范调用方式：
# if __name__ == "__main__":
#     visualizer = Excel3DVisualizer()
#     visualizer.run_gui()
