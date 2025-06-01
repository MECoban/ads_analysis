import pandas as pd
import numpy as np

def calculate_kpis_for_bv5_may23_analysis(df):
    kpi_df = df.copy()
    cols_to_ensure_numeric = ['Amount spent (USD)', 'Impressions', 'Link clicks', 'Reach', 'Results']
    for col in cols_to_ensure_numeric:
        if col in kpi_df.columns:
            kpi_df[col] = pd.to_numeric(kpi_df[col], errors='coerce').fillna(0)
        else:
            print(f"Warning from bv5_may23_analyzer: Expected column '{col}' not found in DataFrame. It will be initialized to 0.")
            kpi_df[col] = 0

    kpi_df['CTR (%)'] = np.where(kpi_df['Impressions'] > 0, (kpi_df['Link clicks'] / kpi_df['Impressions']) * 100, 0)
    kpi_df['CPC (USD)'] = np.where(kpi_df['Link clicks'] > 0, kpi_df['Amount spent (USD)'] / kpi_df['Link clicks'], 0)
    kpi_df['CPM (USD)'] = np.where(kpi_df['Impressions'] > 0, (kpi_df['Amount spent (USD)'] / kpi_df['Impressions']) * 1000, 0)
    return kpi_df

def analyze_ad_sets_bv5_may23(input_df, target_countries, filter_type, top_n=10):
    """
    Analyzes ad set performance for the BV5 May 23-29 dataset.
    Args:
        input_df (pd.DataFrame): DataFrame with ad-level data including 'Country', 'Campaign name', etc.
        target_countries (list): Country codes for filtering.
        filter_type (str): 'include' or 'exclude'.
        top_n (int): Number of top ad sets.
    Returns:
        tuple: (top_by_results_df, top_by_spent_df)
    """
    if 'Campaign name' not in input_df.columns:
        print("Error from bv5_may23_analyzer.analyze_ad_sets_bv5_may23: 'Campaign name' column not found.")
        return pd.DataFrame(), pd.DataFrame()

    df_analysis_ready = input_df.copy()

    if filter_type == 'include':
        df_filtered = df_analysis_ready[df_analysis_ready['Country'].isin(target_countries)]
    elif filter_type == 'exclude':
        df_filtered = df_analysis_ready[~df_analysis_ready['Country'].isin(target_countries)]
    else:
        print(f"Error from bv5_may23_analyzer.analyze_ad_sets_bv5_may23: Invalid filter_type '{filter_type}'.")
        return pd.DataFrame(), pd.DataFrame()

    # --- Temporary Debugging ---
    print(f"--- Debug bv5_may23_analyzer (Dataset: BV5 23-29 May): filter_type='{filter_type}', target_countries={target_countries} ---")
    if not df_filtered.empty:
        print(f"Shape of df_filtered: {df_filtered.shape}")
        print(f"Countries in df_filtered: {df_filtered['Country'].unique()}")
        print(f"Campaign names in df_filtered (first 5): {df_filtered['Campaign name'].unique()[:5]}")
        # Print sum of key metrics to see if they are all zero
        print(f"Sum of 'Amount spent (USD)' in df_filtered: {df_filtered['Amount spent (USD)'].sum()}")
        print(f"Sum of 'Results' in df_filtered: {df_filtered['Results'].sum()}")
        print(f"Sample of df_filtered (head 3):\n{df_filtered.head(3)}")
    else:
        print("df_filtered is empty after country selection for BV5 23-29 May.")
    # --- End Temporary Debugging ---

    if df_filtered.empty:
        return pd.DataFrame(), pd.DataFrame()

    required_metrics = ['Amount spent (USD)', 'Impressions', 'Link clicks', 'Reach', 'Results']
    for metric in required_metrics:
        if metric not in df_filtered.columns:
            print(f"Warning from bv5_may23_analyzer.analyze_ad_sets_bv5_may23: Metric column '{metric}' not found. Treated as 0.")
            df_filtered.loc[:, metric] = 0
        else:
            df_filtered.loc[:, metric] = pd.to_numeric(df_filtered[metric], errors='coerce').fillna(0)

    ad_set_summary = df_filtered.groupby('Campaign name').agg(
        agg_spent=('Amount spent (USD)', 'sum'),
        agg_impressions=('Impressions', 'sum'),
        agg_link_clicks=('Link clicks', 'sum'),
        agg_reach=('Reach', 'sum'),
        agg_results=('Results', 'sum')
    ).reset_index()

    if ad_set_summary.empty:
        return pd.DataFrame(), pd.DataFrame()

    ad_set_summary_renamed = ad_set_summary.rename(columns={
        'agg_spent': 'Amount spent (USD)',
        'agg_impressions': 'Impressions',
        'agg_link_clicks': 'Link clicks',
        'agg_reach': 'Reach',
        'agg_results': 'Results'
    })

    ad_set_kpis_df = calculate_kpis_for_bv5_may23_analysis(ad_set_summary_renamed)

    ad_set_kpis_df['Avg. Cost per Result (USD)'] = np.where(
        ad_set_kpis_df['Results'] > 0,
        ad_set_kpis_df['Amount spent (USD)'] / ad_set_kpis_df['Results'],
        0
    )

    ad_set_kpis_df = ad_set_kpis_df.rename(columns={
        'Amount spent (USD)': 'Total Spent (USD)',
        'Impressions': 'Total Impressions',
        'Link clicks': 'Total Link Clicks',
        'Reach': 'Total Reach',
        'Results': 'Total Results'
    })

    top_by_results_df = ad_set_kpis_df.sort_values(by='Total Results', ascending=False).head(top_n)
    top_by_spent_df = ad_set_kpis_df.sort_values(by='Total Spent (USD)', ascending=False).head(top_n)

    return top_by_results_df, top_by_spent_df 