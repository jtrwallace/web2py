# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

from datetime import datetime, timedelta
from gluon import utils as gluon_utils
import json
import calendar

def index():
    redirect(URL('default', 'boards'))
    return 0

def boards():
    return dict()

def load_boards():
    #Want to serve up all completed boards as well as all drafts that belong only to the user.
    not_draft_boards_query = (db.boards.is_draft == False)
    my_drafts_boards_query = (db.boards.board_author == auth.user_id) & (db.boards.is_draft == True)
    not_drafts = db(not_draft_boards_query)
    my_drafts = db(my_drafts_boards_query)
    all_boards = not_drafts.select() & my_drafts.select()
    for board in all_boards:
        board['total_count'] = len(db(db.posts.board_id == board.id).select())
        board['new_today'] = len(db((db.posts.board_id == board.id) & (db.posts.posting_time >= (datetime.utcnow() - timedelta(days=1)))).select())
    return response.json(list(all_boards))

def board():
    board_id = request.args(0)
    return locals()

def load_posts():
    board = db(db.boards.board_id == request.vars.board_id).select().first()
    my_drafts_query = (db.posts.is_draft == True) & (db.posts.post_author == auth.user_id) & (db.posts.board_id == board.id)
    all_completed_posts_query = (db.posts.board_id == board.id) & (db.posts.is_draft == False)
    my_drafts = db(my_drafts_query)
    all_completed_posts = db(all_completed_posts_query)
    board_posts = my_drafts.select() | all_completed_posts.select()
    return response.json(list(board_posts))

def load_single_board():
    board = db(db.boards.board_id == request.vars.board_id).select().first()
    return response.json(board)

@auth.requires_signature()
def add_board():
    db.boards.update_or_insert((db.boards.board_id == request.vars.board_id),
            board_id=request.vars.board_id,
            board_name=request.vars.board_name,
            board_description=request.vars.board_description,
            is_draft=json.loads(request.vars.is_draft),
            active_draft_description=request.vars.active_draft_description,
            active_draft_name=request.vars.active_draft_name,
            board_last_updated=request.vars.board_last_updated,
            board_pretty_updated=request.vars.board_pretty_updated
            )
    return "ok"

@auth.requires_signature()
def del_board():
    db(db.boards.board_id == request.vars.board_id).delete()
    return "ok"

@auth.requires_signature()
def add_post():
    db.posts.update_or_insert((db.posts.post_id == request.vars.post_id),
            post_id=request.vars.post_id,
            post_title=request.vars.post_title,
            post_content=request.vars.post_content,
            is_draft=json.loads(request.vars.is_draft),
            active_draft_content=request.vars.active_draft_content,
            active_draft_title=request.vars.active_draft_title,
            posting_time=request.vars.posting_time,
            posting_time_pretty=request.vars.posting_time_pretty,
            board_id=request.vars.board_id
            )
    db.boards.update_or_insert((db.boards.id == request.vars.board_id),
            board_last_updated=request.vars.posting_time,
            board_pretty_updated=request.vars.posting_time_pretty
            )
    return "ok"

@auth.requires_signature()
def del_post():
    db(db.posts.post_id == request.vars.post_id).delete()
    return "ok"

@auth.requires_signature()
def edit_post():
    post = db.posts(request.args(0))
    board = post.board_id
    db.posts.posting_time.readable = db.posts.posting_time.writable = False
    db.posts.post_author.readable = db.posts.post_author.writable = False
    db.posts.board_id.readable = db.posts.board_id.writable = False
    db.posts.posting_time_pretty.readable = db.posts.posting_time_pretty.writable = False
    db.posts.id.readable = db.posts.id.writable = False
    form=SQLFORM(db.posts, post)
    if form.process().accepted:
        board.board_last_updated = datetime.utcnow()
        board.update_record()
        try:
            db.commit()
        except Exception , e:
            logger.warning("Transaction commit failed while updating board time")
            redirect(URL('default', 'edit_post', args=[post.id, board.id]))
        redirect(URL('default', 'board', args=board.id))
    return dict(board=board, form=form)

def date():
    date = datetime.utcnow()
    return response.json(date);

def pretty_date():
    date = datetime.utcnow()
    month_abr = calendar.month_abbr[date.month]
    pretty = month_abr + " " + str(date.day) + " " + str(date.time().strftime("%H:%M"))
    return response.json(pretty);

def pretty_date(date):
    month_abr = calendar.month_abbr[date.month]
    pretty = month_abr + " " + str(date.day) + " " + str(date.time().strftime("%H:%M"))
    return pretty

def user():
    return dict(form=auth())


@cache.action()
def download():
    return response.download(request, db)


def call():
    return service()


