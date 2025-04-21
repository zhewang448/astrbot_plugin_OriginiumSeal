from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import os
from PIL import Image
import io
import aiohttp

@register("OriginiumSeal", "FengYing", "让你的头像被源石封印()", "1.0.0", "https://github.com/FengYing1314/astrbot_plugin_OriginiumSeal")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 初始化时设置印章图片路径
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.seal_image_path = os.path.join(self.plugin_dir, "Sealed.png")
        if not os.path.exists(self.seal_image_path):
            logger.info(f"印章图片不存在: {self.seal_image_path}")
            
    @filter.command("制作源石头像")
    async def make_sealed_avatar(self, event: AstrMessageEvent):
        '''当用户发送"制作源石头像"时，将其头像加上"封印"效果'''
        try:
            # 1. 获取发送者信息
            sender_id = event.get_sender_id()
            
            # 2. 检查印章图片是否存在
            if not os.path.exists(self.seal_image_path):
                yield event.plain_result("无法处理头像: 印章图片不存在")
                return
            
            # 3. 获取用户头像
            avatar_url = f"https://q1.qlogo.cn/g?b=qq&nk={sender_id}&s=640"
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as response:
                    if response.status != 200:
                        yield event.plain_result(f"获取头像失败: HTTP {response.status}")
                        return
                    avatar_data = await response.read()
            
            # 4. 处理头像图片
            # 4.1 加载图片
            avatar_img = Image.open(io.BytesIO(avatar_data))
            seal_img = Image.open(self.seal_image_path).convert("RGBA")
            
            # 4.2 调整印章大小
            seal_img = seal_img.resize(avatar_img.size)
            
            # 4.3 设置印章透明度(70%)
            r, g, b, a = seal_img.split()
            a = a.point(lambda i: i * 0.7)
            seal_img = Image.merge('RGBA', (r, g, b, a))
            
            # 4.4 合成图片
            if avatar_img.mode != 'RGBA':
                avatar_img = avatar_img.convert('RGBA')
            result_img = Image.alpha_composite(avatar_img, seal_img)
            
            # 5. 保存处理后的图片到临时文件
            img_bytes = io.BytesIO()
            result_img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            temp_img_path = os.path.join(self.plugin_dir, f"temp_seal_{sender_id}.png")
            with open(temp_img_path, "wb") as f:
                f.write(img_bytes.getvalue())
            
            # 6. 发送处理后的图片
            yield event.image_result(temp_img_path)
            
            # 7. 清理临时文件
            try:
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"处理头像时出错: {str(e)}")
            yield event.plain_result(f"处理头像时出错: {str(e)}")

    async def terminate(self):
        pass
