# ABOUTME: Reusable chart components for X-Tracker UI
# ABOUTME: Professional visualizations using Plotly for growth and analytics data

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

def create_growth_chart(data: List[Dict], title: str = "Growth Metrics") -> go.Figure:
    """Create a growth chart with followers, following, and tweets"""
    if not data:
        return create_empty_chart("No data available")
    
    df = pd.DataFrame(data)
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = go.Figure()
    
    # Followers line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['followers_count'],
        name='Followers',
        line=dict(color='#3B82F6', width=3),
        hovertemplate='<b>Followers</b><br>Date: %{x}<br>Count: %{y:,}<extra></extra>'
    ))
    
    # Following line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['following_count'],
        name='Following',
        line=dict(color='#EF4444', width=2),
        hovertemplate='<b>Following</b><br>Date: %{x}<br>Count: %{y:,}<extra></extra>'
    ))
    
    # Tweets line (secondary y-axis)
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['tweet_count'],
        name='Tweets',
        line=dict(color='#10B981', width=2),
        yaxis='y2',
        hovertemplate='<b>Tweets</b><br>Date: %{x}<br>Count: %{y:,}<extra></extra>'
    ))
    
    # Layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Followers / Following",
        yaxis2=dict(
            title="Tweets",
            overlaying='y',
            side='right',
            color='#10B981'
        ),
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=80, t=50, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_velocity_chart(data: List[Dict], title: str = "Growth Velocity") -> go.Figure:
    """Create velocity chart showing followers per hour"""
    if not data:
        return create_empty_chart("No velocity data available")
    
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filter out extreme values for better visualization
    df = df[df['follower_velocity'].between(-100, 100)]
    
    fig = go.Figure()
    
    # Velocity bars
    colors = ['#EF4444' if v < 0 else '#10B981' for v in df['follower_velocity']]
    
    fig.add_trace(go.Bar(
        x=df['timestamp'],
        y=df['follower_velocity'],
        name='Follower Velocity',
        marker_color=colors,
        hovertemplate='<b>Growth Velocity</b><br>Date: %{x}<br>Rate: %{y:.2f} followers/hour<extra></extra>'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Followers per Hour",
        template='plotly_white',
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=False
    )
    
    return fig

def create_competitor_chart(competitors_data: List[Dict], title: str = "Competitor Analysis") -> go.Figure:
    """Create competitor comparison chart"""
    if not competitors_data:
        return create_empty_chart("No competitor data available")
    
    fig = go.Figure()
    
    for competitor in competitors_data:
        name = competitor.get('name', competitor.get('username', 'Unknown'))
        data = competitor.get('data', [])
        
        if not data:
            continue
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['followers_count'],
            name=f"@{name}",
            line=dict(width=2),
            hovertemplate=f'<b>{name}</b><br>Date: %{{x}}<br>Followers: %{{y:,}}<extra></extra>'
        ))
    
    # Layout
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Followers",
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_unfollow_analysis_chart(data: List[Dict], title: str = "Unfollow Analysis") -> go.Figure:
    """Create chart showing unfollow patterns"""
    if not data:
        return create_empty_chart("No unfollow data available")
    
    df = pd.DataFrame(data)
    
    # Group by reason
    reason_counts = df.groupby('reason').size().reset_index(name='count')
    
    fig = go.Figure(data=[
        go.Pie(
            labels=reason_counts['reason'],
            values=reason_counts['count'],
            hole=0.4,
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=True,
        annotations=[dict(text='Unfollows', x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    
    return fig

def create_activity_heatmap(data: List[Dict], title: str = "Activity Heatmap") -> go.Figure:
    """Create heatmap showing activity patterns"""
    if not data:
        return create_empty_chart("No activity data available")
    
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['day'] = df['timestamp'].dt.day_name()
    
    # Create pivot table for heatmap
    heatmap_data = df.groupby(['day', 'hour']).size().unstack(fill_value=0)
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(day_order)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[f"{h}:00" for h in range(24)],
        y=day_order,
        colorscale='Viridis',
        hovertemplate='<b>%{y}</b><br>Hour: %{x}<br>Activity: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        template='plotly_white',
        height=300,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def create_metrics_summary(metrics: Dict[str, Any]) -> go.Figure:
    """Create summary metrics card visualization"""
    
    # Create a simple metrics display
    fig = go.Figure()
    
    # Add invisible trace for proper scaling
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='markers', marker=dict(size=0), showlegend=False))
    
    # Add metric annotations
    metrics_list = [
        ("Followers", metrics.get('followers_count', 0), "#3B82F6"),
        ("Following", metrics.get('following_count', 0), "#EF4444"),
        ("Tweets", metrics.get('tweet_count', 0), "#10B981"),
        ("Listed", metrics.get('listed_count', 0), "#F59E0B")
    ]
    
    for i, (label, value, color) in enumerate(metrics_list):
        x_pos = 0.2 + (i % 2) * 0.6
        y_pos = 0.7 if i < 2 else 0.3
        
        fig.add_annotation(
            x=x_pos, y=y_pos,
            text=f"<b style='color:{color}'>{value:,}</b><br>{label}",
            showarrow=False,
            font=dict(size=16),
            align="center"
        )
    
    fig.update_layout(
        title="Current Metrics",
        showlegend=False,
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
        template='plotly_white',
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def create_empty_chart(message: str = "No data available") -> go.Figure:
    """Create empty chart with message"""
    fig = go.Figure()
    
    fig.add_annotation(
        x=0.5, y=0.5,
        text=message,
        showarrow=False,
        font=dict(size=16, color="gray"),
        align="center"
    )
    
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        template='plotly_white',
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    return fig