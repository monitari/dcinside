import json
import os

def calculate_and_generate_html(posts, target_date, gallery_info):
    # 통계 계산
    total_posts = 0
    user_counts = {}
    for key, info in posts.items():
        cnt = len(info['titles'])
        user_counts[key] = cnt
        total_posts += cnt

    ranking = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)
    stats = {
        "total_posts": total_posts,
        "ranking": ranking,
        "user_shares": [
            {
                "user": user,
                "share": round((count / total_posts) * 100, 2)
            }
            for user, count in ranking
        ]
    }
    stats["total_users"] = len(posts)
    stats["average_posts"] = round(total_posts / len(posts), 2) if posts else 0

    result = {
        "posts": posts,
        "stats": stats
    }

    # posts.json에 posts만 저장
    posts_str = json.dumps(result["posts"], ensure_ascii=False, indent=4, separators=(',', ':'))
    with open('posts.json', 'w', encoding='utf-8') as f:
        f.write(posts_str)

    # 새 메트릭 계산: view, recommend, comment 및 total score
    view_scores = {}
    recommend_scores = {}
    comment_scores = {}
    total_scores = {}
    for user, info in posts.items():
        total_view = total_recommend = total_comment = 0
        for title_info in info['titles']:
            parts = title_info.split('|')
            # parts[0] = 제목, parts[1] = 조회수, parts[2] = 추천수, parts[3] = 작성일 (댓글수 없음 시 0)
            try:
                view = int(parts[1].strip())
            except:
                view = 0
            try:
                recommend = int(parts[2].strip())
            except:
                recommend = 0
            # 댓글수: 있으면 parts[3] 혹은 기본 0 (현재 게시글에 댓글수 정보가 없음)
            comment = 0
            if len(parts) >= 5:
                try:
                    comment = int(parts[3].strip())
                except:
                    comment = 0
            total_view += view
            total_recommend += recommend
            total_comment += comment
        view_scores[user] = total_view
        recommend_scores[user] = total_recommend
        comment_scores[user] = total_comment
        total_scores[user] = total_view + total_recommend + total_comment + user_counts.get(user, 0)

    view_ranking = sorted(view_scores.items(), key=lambda x: x[1], reverse=True)
    recommend_ranking = sorted(recommend_scores.items(), key=lambda x: x[1], reverse=True)
    comment_ranking = sorted(comment_scores.items(), key=lambda x: x[1], reverse=True)
    total_ranking = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)

    # 공통 테이블 행 생성 함수 (지분 포함 옵션 지원)
    def build_table_rows(ranking_list, posts_dict, include_share=False):
      rows = ""
      current_rank = 1
      previous_value = None
      for idx, (user, value) in enumerate(ranking_list):
        if previous_value is None or previous_value != value: current_rank = idx + 1
        previous_value = value
        nickname = posts_dict.get(user, {}).get("writer", "알수없음")
        if include_share:
          share = next((item["share"] for item in stats["user_shares"] if item["user"] == user), 0)
          rows += f"<tr><td>{current_rank}</td><td>{nickname}</td><td>{user}</td><td>{value}</td><td>{share}</td></tr>\n"
        else: rows += f"<tr><td>{current_rank}</td><td>{nickname}</td><td>{user}</td><td>{value}</td></tr>\n"          
        # 게시글 목록 추가
        user_titles = posts_dict.get(user, {}).get("titles", [])
        if user_titles:
            title_list = "<br>".join(title.split('|')[0] for title in user_titles)
            colspan = "5" if include_share else "4"
            # 게시글 목록을 details 태그로 감싸서 기본 접힌 상태로 변경
            rows += f"<tr><td colspan='{colspan}' style='padding:0;'><details><summary>게시글 목록</summary><div style='font-size:0.9rem; color:#666;'>{title_list}</div></details></td></tr>\n"
      return rows

    # 기존 랭킹 테이블 생성 (지분 표시 포함)
    ranking_rows = build_table_rows(stats["ranking"], result["posts"], include_share=True)

    # 각 메트릭(조회수, 추천수, 댓글수, 총 점수)에 대해 랭킹 테이블 생성
    view_ranking_rows = build_table_rows(view_ranking, result["posts"])
    recommend_ranking_rows = build_table_rows(recommend_ranking, result["posts"])
    comment_ranking_rows = build_table_rows(comment_ranking, result["posts"])
    total_ranking_rows = build_table_rows(total_ranking, result["posts"])

    view_ranking_rows = build_table_rows(view_ranking, result["posts"])
    recommend_ranking_rows = build_table_rows(recommend_ranking, result["posts"])
    comment_ranking_rows = build_table_rows(comment_ranking, result["posts"])
    total_ranking_rows = build_table_rows(total_ranking, result["posts"])

    # HTML 파일 생성 (랭킹 테이블 섹션 확장)
    report_path = os.path.join(os.path.dirname(__file__), "templates", "report.html")
    with open(report_path, "r", encoding="utf-8") as t:
        html_content = t.read()
    html_result = html_content.format(
        total_posts=stats["total_posts"],
        total_users=stats["total_users"],
        average_posts=stats["average_posts"],
        ranking_rows=ranking_rows,
        view_ranking_rows=view_ranking_rows,
        recommend_ranking_rows=recommend_ranking_rows,
        comment_ranking_rows=comment_ranking_rows,
        total_ranking_rows=total_ranking_rows,
        target_date=target_date,
        name=gallery_info.get("name", "Unknown"),
        cover=gallery_info.get("cover", ""),
        intro=gallery_info.get("intro", "-"),
        manager=gallery_info.get("manager", "없음"),
        sub_manager=gallery_info.get("sub_manager", "없음"),
        creation_date=gallery_info.get("creation_date", "정보 없음"),
        rank_text=gallery_info.get("rank_text", ""),
        rank_num=gallery_info.get("rank_num", "")
    )

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_result)
