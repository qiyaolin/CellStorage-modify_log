@echo off
echo Testing print API with curl...

echo.
echo 1. Testing print service status:
curl -X GET "https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/status" -H "Authorization: Bearer zWCcDs_VmMWYVs6xWudyOZlRCwwC4Q-PAmKmrNpZ_kI"

echo.
echo.
echo 2. Testing fetch pending job:
curl -X GET "https://ambient-decoder-467517-h8.nn.r.appspot.com/api/print/fetch-pending-job?server_id=test" -H "Authorization: Bearer zWCcDs_VmMWYVs6xWudyOZlRCwwC4Q-PAmKmrNpZ_kI"

echo.
echo.
echo Done!
pause