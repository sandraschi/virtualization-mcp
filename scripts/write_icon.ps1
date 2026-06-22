$base64 = 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAADUlEQVR42mP8/5+hHgAGgwJ/l7XhYwAAAABJRU5ErkJggg=='
[IO.File]::WriteAllBytes('D:/Dev/repos/virtualization-mcp/assets/icon.png', [System.Convert]::FromBase64String($base64))
