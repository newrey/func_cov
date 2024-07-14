import pandas as pd
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State

# 读取初始的 CSV 文件
df = pd.read_csv('connections.csv')

# 确保 'Reviewed' 列存在于初始 DataFrame 中
if 'Reviewed' not in df.columns:
    df['Reviewed'] = False

# 初始化 Dash 应用程序
app = dash.Dash(__name__)

# 定义应用程序布局
app.layout = html.Div([
    html.H1('CSV 数据查看器'),

    # 筛选条件下拉框
    html.Label('按 SRC_MODULE 筛选：'),
    dcc.Dropdown(
        id='src-module-filter',
        options=[{'label': module, 'value': module} for module in df['SRC_MODULE'].unique()],
        multi=True,
        value=[]  # 初始值为空列表
    ),

    html.Label('按 SRC_SIG 筛选：'),
    dcc.Dropdown(
        id='src-sig-filter',
        options=[{'label': sig, 'value': sig} for sig in df['SRC_SIG'].unique()],
        multi=True,
        value=[]  # 初始值为空列表
    ),

    html.Label('按 DST_MODULE 筛选：'),
    dcc.Dropdown(
        id='dst-module-filter',
        options=[{'label': module, 'value': module} for module in df['DST_MODULE'].unique()],
        multi=True,
        value=[]  # 初始值为空列表
    ),

    html.Label('按 DST_SIG 筛选：'),
    dcc.Dropdown(
        id='dst-sig-filter',
        options=[{'label': sig, 'value': sig} for sig in df['DST_SIG'].unique()],
        multi=True,
        value=[]  # 初始值为空列表
    ),

    # 展示数据的表格
    html.Div(id='datatable-container', children=[
        dash_table.DataTable(
            id='datatable',
            columns=[
                {'name': col, 'id': col, 'editable': True if col == 'Reviewed' else False}  # 'Reviewed' 列可编辑
                for col in df.columns
            ],
            data=df.to_dict('records'),
            filter_action='native',  # 启用列筛选
            sort_action='native',    # 启用列排序
            page_size=10,            # 每页显示 10 行
            row_selectable='multi',  # 允许多行选择
            selected_rows=[]         # 初始化选中行为空列表
        )
    ]),

    # 审核按钮
    html.Button('审核选中行', id='review-button', n_clicks=0),

    # 审核状态消息
    html.Div(id='review-status')
])

# 定义回调函数以根据筛选条件更新表格数据和处理审核按钮点击事件
@app.callback(
    [Output('datatable', 'data'), Output('review-status', 'children')],
    [Input('src-module-filter', 'value'),
     Input('src-sig-filter', 'value'),
     Input('dst-module-filter', 'value'),
     Input('dst-sig-filter', 'value'),
     Input('review-button', 'n_clicks')],
    [State('datatable', 'selected_rows'),
     State('datatable', 'data')]
)
def update_datatable_and_review_status(src_module_values, src_sig_values, dst_module_values, dst_sig_values, n_clicks, selected_rows, table_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        # 没有触发器，返回不更新
        return dash.no_update, dash.no_update
    
    # 确定触发回调的输入组件
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # 根据筛选条件更新表格数据
    if trigger_id in ['src-module-filter', 'src-sig-filter', 'dst-module-filter', 'dst-sig-filter']:
        filtered_df = df.copy()
        if src_module_values:
            filtered_df = filtered_df[filtered_df['SRC_MODULE'].isin(src_module_values)]
        if src_sig_values:
            filtered_df = filtered_df[filtered_df['SRC_SIG'].isin(src_sig_values)]
        if dst_module_values:
            filtered_df = filtered_df[filtered_df['DST_MODULE'].isin(dst_module_values)]
        if dst_sig_values:
            filtered_df = filtered_df[filtered_df['DST_SIG'].isin(dst_sig_values)]
        
        return filtered_df.to_dict('records'), dash.no_update
    
    # 处理审核按钮点击事件
    if n_clicks > 0:
        if len(selected_rows) == 0:
            return dash.no_update, html.Div('请先选择要审核的行。')
        
        for idx in selected_rows:
            if idx < len(table_data):
                table_data[idx]['Reviewed'] = True
                df.at[idx, 'Reviewed'] = True
        
        # 将更新后的数据保存回 CSV 文件
        df.to_csv('connections.csv', index=False)

        return df.to_dict('records'), html.Div(f'已审核 {len(selected_rows)} 行。数据已保存。')
    
    return dash.no_update, dash.no_update

# 启动应用程序
if __name__ == '__main__':
    app.run_server(debug=False)
