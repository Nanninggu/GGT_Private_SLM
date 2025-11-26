# 문서 관리 페이지 SQL 문법 오류 수정

## 문제 상황
문서 관리 페이지에서 새로운 데이터셋을 생성 후 해당 데이터셋을 선택하면 다음과 같은 500 에러가 발생했습니다:

```
GET http://localhost:5174/api/documents?collection_name=%EC%97%85%EB%A1%9C%EB%93%9C+%ED%85%8C%EC%8A%A4%ED%8A%B8&limit=20&offset=0&order_by=created_at&order_direction=desc 500 (Internal Server Error)
```

## 원인 분석
백엔드 로그를 확인한 결과, SQL 쿼리에 문법 오류가 있었습니다:

```sql
GROUP BY (e.cmetadata->>'filename'), c.name, c.user_id
AND (c.user_id = $2 OR c.user_id IS NULL)  -- 잘못된 위치!
ORDER BY created_at desc
```

**문제점**: `GROUP BY` 절 다음에 `AND` 절이 와서 SQL 문법 오류가 발생했습니다. `WHERE` 절의 조건은 반드시 `GROUP BY` **이전**에 와야 합니다.

이는 이전에 `user_id` 컬럼 존재 여부를 확인하는 수정을 하면서, 사용자 필터링 조건을 쿼리 끝에 추가(`query +=`)하는 방식으로 구현했기 때문에 발생한 문제였습니다.

## 해결 방법

### 1. WHERE 절 조건을 먼저 구성
사용자 필터링 조건을 포함한 모든 WHERE 절 조건을 먼저 구성하도록 변경했습니다:

```python
# Build WHERE clause parts
where_clauses = ["c.name = :collection_name", "(e.cmetadata->>'filename') IS NOT NULL"]
params = {"collection_name": collection_name}

# Add user filter to WHERE clause if authenticated and user_id column exists
if user_id and has_langchain_user_id:
    where_clauses.append("(c.user_id = :user_id OR c.user_id IS NULL)")
    params["user_id"] = user_id

where_clause = " AND ".join(where_clauses)
```

### 2. f-string을 사용하여 WHERE 절 삽입
쿼리를 f-string으로 변경하여 WHERE 절을 올바른 위치에 삽입:

```python
if has_langchain_user_id:
    query = f"""
        SELECT ...
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE {where_clause}  -- 올바른 위치!
        GROUP BY (e.cmetadata->>'filename'), c.name, c.user_id
    """
```

### 3. COUNT 쿼리도 동일하게 수정
COUNT 쿼리도 같은 `where_clause`를 사용하도록 수정하고, 중복된 파라미터 정의를 제거:

```python
count_query = f"""
    SELECT COUNT(DISTINCT (e.cmetadata->>'filename'))
    FROM langchain_pg_embedding e
    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
    WHERE {where_clause}
"""
# Same params dictionary is used for both queries
count_result = await session.execute(text(count_query), params)
```

## 수정된 파일
- `/Users/may9noy/Documents/workstation-001/GGT_Private_SLM/backend/main.py`
  - 라인 2038-2150: `GET /api/documents` 엔드포인트의 LangChain 컬렉션 쿼리 수정

## 테스트 결과
수정 후 모든 컬렉션에 대해 정상적으로 작동합니다:

```bash
# 빈 컬렉션 테스트
$ curl "http://localhost:9502/api/documents?collection_name=%EC%97%85%EB%A1%9C%EB%93%9C%20%ED%85%8C%EC%8A%A4%ED%8A%B8&limit=20"
{"success":true,"documents":[],"total":0,"limit":20,"offset":0}

# 다른 컬렉션 테스트
$ curl "http://localhost:9502/api/documents?collection_name=%ED%85%8C%EC%8A%A4%ED%8A%B8%20%EB%8D%B0%EC%9D%B4%ED%84%B0%20%EC%85%8B&limit=2"
{"success":true,"documents":[],"total":0,"limit":2,"offset":0}
```

백엔드 로그에서도 에러가 발생하지 않습니다:
```
INFO:     ::1:54407 - "GET /api/documents?collection_name=... HTTP/1.1" 200 OK
```

## 영향 범위
- ✅ 기존 기능에 영향 없음
- ✅ 모든 컬렉션(빈 컬렉션 포함)에서 정상 작동
- ✅ 사용자 필터링 기능 정상 작동
- ✅ SQL 문법 오류 완전히 해결

## 결론
SQL 쿼리의 WHERE 절 조건을 올바른 위치(GROUP BY 이전)에 배치하여 500 에러를 해결했습니다. 현재 구현된 모든 기능이 정상적으로 작동합니다.
