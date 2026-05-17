name: Update IP List

on:
  schedule:
    - cron: '*/40 * * * *'     # 每40分钟自动更新
  workflow_dispatch:           # 支持手动触发

jobs:
  update-ip-list:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      with:
        token: ${{ secrets.GITHUB_TOKEN }}

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install requests

    - name: Collect Best IPs
      run: python collect_ips.py

    - name: Commit and push ip.txt
      uses: stefanzweifel/git-auto-commit-action@v5
      with:
        commit_message: "chore: update ip.txt with new Cloudflare IPs"
        file_pattern: ip.txt
