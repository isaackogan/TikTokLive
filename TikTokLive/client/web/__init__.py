
# Dummy class for type hinting
class curl_cffi_dummy:
    class requests:
        class Response:
            pass

        class AsyncSession:
            async def close(self):
                pass

            async def request(self, *args, **kwargs) -> "curl_cffi_dummy.requests.Response":
                pass