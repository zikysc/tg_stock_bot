"""
Telegram Stock Analysis Bot
Copyright (c) zikysc. All Rights Reserved.

Dispatcher: 提供生成股票K线图的功能
"""

import logging
import os
import pandas as pd
import mplfinance as mpf
import matplotlib

# 必须在导入 pyplot 之前设置后端
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

def generate_candlestick_image(stock_code: str, kline_data: list, days: int = 60):
    if not kline_data or len(kline_data) < 5:
        logging.error(f"[{stock_code}] 数据量太少无法绘图")
        return None

    img_path = f"./kline_{stock_code}.png"

    try:
        df = pd.DataFrame(kline_data)
        df = df.rename(columns={
            'date': 'Date', 'open': 'Open', 'high': 'High',
            'low': 'Low', 'close': 'Close', 'volume': 'Volume'
        })
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df = df.sort_index()

        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()

        plot_df = df.tail(days)

        mc = mpf.make_marketcolors(up='red', down='green', edge='inherit',
                                   wick='inherit', volume='inherit')
        s = mpf.make_mpf_style(base_mpf_style='charles', marketcolors=mc,
                               gridstyle='--', y_on_right=True)

        apds = [
            mpf.make_addplot(plot_df['MA5'], color='#FF8C00', width=1.0),
            mpf.make_addplot(plot_df['MA20'], color='#1E90FF', width=1.0),
            mpf.make_addplot(plot_df['MA60'], color='#FF1493', width=1.5)
        ]

        fig, axes = mpf.plot(
            plot_df, type='candle', addplot=apds, style=s, volume=True,
            figratio=(20, 11),
            title=f"\nStock: {stock_code} (Updated to {plot_df.index[-1].strftime('%m-%d')})",
            ylabel='Price', ylabel_lower='Volume',
            returnfig=True, tight_layout=True
        )

        ax_kline, ax_vol = axes[0], axes[2]
        custom_lines = [Line2D([0], [0], color=c, lw=2) for c in ['#FF8C00', '#1E90FF', '#FF1493']]
        ax_kline.legend(custom_lines, ['MA5', 'MA20', 'MA60'], loc='upper right', fontsize=10)

        ax_vol.set_xticks([])
        ax_vol.set_xticklabels([])
        ax_vol.set_xlim(-0.5, len(plot_df) - 0.5)

        for ax in fig.get_axes():
            for spine in ax.spines.values():
                spine.set_visible(False)

        fig.savefig(img_path, dpi=120, bbox_inches='tight')
        plt.close(fig)
        return img_path

    except Exception as e:
        logging.error(f"生成K线图异常: {e}")
        if 'fig' in locals():
            plt.close(fig)
        return None