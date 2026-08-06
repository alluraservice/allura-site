import dash
from dash import html
from database import db_handler
from allurasite_public.components import render_social_icons_row

dash.register_page(__name__, path='/news', title='Allura Enterprise - News/Blog')


def render_news_card(post):
    return html.Div(className='news-card', children=[
        html.Div(className='news-card-image-wrap', children=[
            html.Img(src=post.get('image'), className='news-card-image', alt=post.get('title', ''))
        ]),
        html.Div(className='news-card-content', children=[
            html.H3(post.get('title'), className='news-card-title'),
            html.Div(
                f"by {post.get('author', '')} | {post.get('post_date', '')}" +
                (f" | {post.get('tags')}" if post.get('tags') else ''),
                className='news-card-meta'
            ),
            html.P(post.get('content'), className='news-card-body')
        ])
    ])


def layout():
    posts = db_handler.get_news_posts()

    return html.Div(className='info-page-wrapper', children=[
        # 1. HERO BANNER
        html.Div(className='info-hero-banner', children=[
            html.Div(className='info-hero-bg'),
            html.Div(className='info-hero-overlay', children=[
                html.H1("NEWS/BLOG", className='info-hero-title')
            ])
        ]),

        # 2. FOLLOW US ROW + NEWS CARDS
        html.Div(className='container', style={'paddingTop': '40px', 'paddingBottom': '60px'}, children=[
            html.Div(className='news-follow-row', children=[
                html.Span("Follow us on:", className='news-follow-label'),
                render_social_icons_row()
            ]),

            html.Div(children=(
                [render_news_card(post) for post in posts]
                if posts else
                [html.Div(className='news-card', children=[
                    html.P("No news/blog posts yet. Add rows to database/news_posts.csv and run database/seed_site_content.py.")
                ])]
            ))
        ])
    ])