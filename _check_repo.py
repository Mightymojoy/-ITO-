with open('product_dashboard.html','r',encoding='utf-8') as f:
    content=f.read()
print('File size:', len(content))
checks=['const LUG_DAILY','const BAG_DAILY','const ALL_DAILY','P2-TRUNK','2026-06','2026-07']
for c in checks:
    ok = 'OK' if c in content else 'MISSING'
    print(f'  {c}: {ok}')
# Check for any JS error signs
if 'Uncaught' in content or 'error' in content.lower()[:5000]:
    print('WARNING: Possible JS errors in first 5000 chars')
else:
    print('No JS errors in first 5000 chars')
