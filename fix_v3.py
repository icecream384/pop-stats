import re

with open('index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. CDN_BASE -> relative
c = c.replace('https://cdn.jsdelivr.net/gh/icecream384/pop-stats@main/data/', 'data/')
print('1. CDN_BASE -> relative: done')

# 2. Remove auto-fit
old = 'map.fitBounds(L.latLngBounds([[Math.min.apply(null,lats)-.01,Math.min.apply(null,lngs)-.01],[Math.max.apply(null,lats)+.01,Math.max.apply(null,lngs)+.01]]).pad(.2))'
c = c.replace(old, '// no auto-fit')
print('2. Remove auto-fit:', 'found' if old in open('index.html','r',encoding='utf-8').read() else 'already done')

# 3. Remove SW block
# Find the SW section boundaries
sw_marker = "if('serviceWorker' in navigator)"
idx = c.find(sw_marker)
if idx >= 0:
    # find the closing };
    end = c.find('}\n', idx)
    end = c.find('\n', end) + 1
    c = c[:idx] + c[end:]
    print('3. Removed SW block')
else:
    print('3. SW block not found')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
