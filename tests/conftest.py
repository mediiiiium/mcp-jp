# tests ディレクトリを import パスに含めるための空 conftest。
# pytest はこのファイルのあるディレクトリを sys.path に追加するため、
# 各テストから `from _discovery import ...` が解決できる。
