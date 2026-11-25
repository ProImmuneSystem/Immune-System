# 면역뉴스 · WordPress → GitHub Pages

워드프레스닷컴은 작성·편집 원본이고, 이 저장소는 검색 공개용 복제 사이트입니다. WordPress 앱에서 글을 발행·수정·공개 해제하면 동기화 작업이 글과 이미지를 가져와 GitHub Pages를 갱신합니다. 본문은 원본 출력 HTML을 사용합니다.

- 현재 저장소 주소: `https://proimmunesystem.github.io/Immune-System/`
- GitHub Actions의 **Sync WordPress and deploy → Run workflow**로 즉시 실행할 수 있습니다. 매시 17분에도 실행되지만 GitHub 예약 실행은 지연되거나 누락될 수 있으므로 1시간 이내 반영을 보장하지 않습니다.
- 글 수정 시간과 본문, 카테고리를 확인하고, 원본의 전체 목록을 정상적으로 받지 못하면 삭제 동작 없이 종료합니다. 공개 해제된 글은 다음 성공한 동기화에서 삭제합니다.
- 이미지 파일은 `assets/images/`에 URL 해시로 저장하고 재다운로드를 피합니다. WordPress의 이미지 이용 권한과 출처를 유지해야 합니다.
- 홈의 고정 주요 기사는 `_data/home.yml`, 메뉴는 `_data/navigation.yml`을 편집합니다. 기사 슬러그를 지정하고 파일을 커밋하면 됩니다.
- 기존 독립형 예약 발행기는 더 이상 배포하지 않습니다. 관련 파일과 기존 원고는 저장소에 남아 있고 이전 워크플로는 Git 기록에서 볼 수 있습니다.

## 설정

저장소 Settings → Pages → Build and deployment → Source에서 **GitHub Actions**를 선택합니다. Settings → Actions → General → Workflow permissions에서 읽기·쓰기 권한이 필요한지 확인합니다. 워크플로는 contents 쓰기와 Pages 배포 권한을 요청합니다. 공개 저장소의 워크플로는 공개 정보만 다루며 별도 인증 토큰을 요구하지 않습니다.

사이트 설정은 `_config.yml`에서 관리합니다. 현재 `url`은 `https://proimmunesystem.github.io`, `baseurl`은 `/Immune-System`입니다. 도메인을 나중에 연결하면 `url`을 해당 `https://도메인`으로 바꾸고 `baseurl`은 빈 문자열로 바꿉니다. Jekyll의 SEO 태그와 사이트맵은 복제 사이트의 주소를 canonical로 사용합니다.

### 네이버·구글 등록

1. 네이버 서치어드바이저에서 위 공개 사이트 주소를 등록합니다.
2. 발급받은 인증 HTML 파일을 저장소 루트에 추가하거나 `_config.yml`의 `naver_verification`에 메타태그의 값만 넣고 커밋합니다. 구글은 `google_verification`에 값을 넣습니다.
3. 배포가 끝나면 `/Immune-System/sitemap.xml`을 제출합니다. `robots.txt`, `/feed.xml`도 자동 제공됩니다. 인증과 색인은 검색엔진 측에서 별도로 진행되며 색인을 보장하지 않습니다.

### 나중에 도메인 연결

소유 도메인을 GitHub Pages 설정에 등록하고, 도메인 DNS의 A 레코드를 `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`으로 지정합니다. `www`를 사용하면 GitHub 공식 안내에 따라 CNAME도 지정합니다. 검증·전파 후 Settings → Pages에서 Enforce HTTPS를 켭니다. `CNAME` 파일은 도메인을 실제로 연결할 때 추가합니다. `_config.yml`의 `url`과 `baseurl`도 함께 변경합니다.

## 로컬 점검

Ruby 3.3과 Bundler에서 `bundle install` 후 `bundle exec jekyll serve`를 실행합니다. WordPress 네트워크가 가능하다면 `python scripts/sync_wp.py`를 실행할 수 있습니다. 이미지 다운로드나 페이지 목록 조회가 실패하면 작업이 오류로 끝나므로, 실패 상태에서 변경을 커밋하지 마세요. 원본 HTML 수집은 `scripts/capture_source.sh`로 실행할 수 있으며 `_source`는 배포하지 않습니다.
