import pandas as pd
import matplotlib.pyplot as plt

file_path = 'C:/Users/user/Documents/Python Scripts/Python Scripts/'

def create_df(file_name):
    full_path = file_path + file_name
    df = pd.read_csv(full_path, sep='\t')
    df.columns = df.columns.str.replace('<', '').str.replace('>', '')
    return df

files = ['AUDNZD_H4.csv', 'AUDNZD_H1.csv', 'AUDNZD_M30.csv', 'EURGBP_H4.csv', 'EURGBP_H1.csv', 'EURCHF_H4.csv', 'EURCHF_H1.csv',
         'EURUSD_H1.csv', 'EURUSD_M30.csv', 'EURUSD_M15.csv', 'GBPUSD_H1.csv', 'GBPUSD_M30.csv', 'GBPUSD_M15.csv', 'NZDUSD_H1.csv',
         'NZDUSD_M30.csv', 'NZDUSD_M15.csv', 'AUDUSD_H1.csv', 'AUDUSD_M30.csv', 'AUDUSD_M15.csv']

# Store data and timeframe as tuple in dictionary
data_dict = {}
for file_name in files:
    data = create_df(file_name)
    timeframe = file_name[file_name.find('_')+1:file_name.find('.')]
    data_dict[file_name] = (data, timeframe)

def get_annual_multiplier(timeframe):
    periods_per_day = {
        'M1': 24 * 60,      # 1-minute: 1440 periods per day
        'M5': 24 * 12,      # 5-minute: 288 periods per day
        'M15': 24 * 4,      # 15-minute: 96 periods per day
        'M30': 24 * 2,      # 30-minute: 48 periods per day
        'H1': 24,           # 1-hour: 24 periods per day
        'H4': 6,            # 4-hour: 6 periods per day
        'D1': 1,            # Daily: 1 period per day
        'W1': 1/7,          # Weekly: 0.14 periods per day
        'MN': 1/30,         # Monthly: 0.033 periods per day
    }
    
    if timeframe not in periods_per_day:
        raise ValueError(f"Unsupported timeframe: {timeframe}. Supported timeframes are: {list(periods_per_day.keys())}")
    
    return 252 * periods_per_day[timeframe]

def calculate_annual_return(total_return, df_length, timeframe):
    annual_periods = get_annual_multiplier(timeframe)
    return (1 + total_return) ** (annual_periods/df_length) - 1

def backtest_reversion_strategy(df, timeframe):  # Added timeframe parameter
    # Calculate 50-day rolling high and low
    df['50_day_high'] = df['CLOSE'].rolling(window=50).max()
    df['50_day_low'] = df['CLOSE'].rolling(window=50).min()
    
    # Initialize position and signals
    df['position'] = 0
    df['signal'] = 0
    df['returns'] = 0.0
    
    current_position = 0
    
    # Generate signals
    for i in range(51, len(df)):
        price = df.iloc[i]['CLOSE']
        high_50 = df.iloc[i-1]['50_day_high']
        low_50 = df.iloc[i-1]['50_day_low']
        
        if current_position == 0:  # No position
           if price > high_50:
               df.iloc[i, df.columns.get_loc('signal')] = -1
               current_position = -1
           elif price < low_50:
               df.iloc[i, df.columns.get_loc('signal')] = 1
               current_position = 1
               
        elif current_position == 1:  # Long position
           if price > high_50:
               df.iloc[i, df.columns.get_loc('signal')] = -1
               current_position = -1

        elif current_position == -1:  # Short position
           if price < low_50:
               df.iloc[i, df.columns.get_loc('signal')] = 1
               current_position = 1
        
        df.iloc[i, df.columns.get_loc('position')] = current_position
    
    # Calculate returns
    df['price_returns'] = df['CLOSE'].pct_change()
    df['strategy_returns'] = df['position'].shift(1) * df['price_returns']
    df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
    
    # Calculate performance metrics
    total_trades = len(df[df['signal'] != 0])
    total_return = df['cumulative_returns'].iloc[-1] - 1
    annual_return = calculate_annual_return(total_return, len(df), timeframe)
    daily_returns = df['strategy_returns'].dropna()
    
    annual_periods = get_annual_multiplier(timeframe)
    sharpe_ratio = (daily_returns.mean() * annual_periods) / (daily_returns.std() * (annual_periods**0.5))
    max_drawdown = (df['cumulative_returns'].cummax() - df['cumulative_returns']).max()
    
    results = {
        'Total Trades': total_trades,
        'Total Return': f"{total_return*100:.2f}%",
        'Annualized Return': f"{annual_return*100:.2f}%",
        'Sharpe Ratio': f"{sharpe_ratio:.2f}",
        'Max Drawdown': f"{max_drawdown*100:.2f}%",
        'Timeframe': timeframe
    }
    
    return df, results

# Run backtest for each instrument and timeframe
results_dict = {}
for file_name, (data, timeframe) in data_dict.items():
    results_dict[file_name] = backtest_reversion_strategy(data, timeframe)

# Optional: Print results for verification
for file_name, (_, results) in results_dict.items():
    print(f"\nResults for {file_name}:")
    for metric, value in results.items():
        print(f"{metric}: {value}")

"""
Results for NZDUSD_M15.csv:
Total Trades: 1400
Total Return: 68.24%
Annualized Return: 13.43%
Sharpe Ratio: 1.19
Max Drawdown: 15.86%
Timeframe: M15

Results for AUDUSD_M15.csv:
Total Trades: 1342
Total Return: 38.85%
Annualized Return: 8.28%
Sharpe Ratio: 0.79
Max Drawdown: 13.87%
Timeframe: M15
"""