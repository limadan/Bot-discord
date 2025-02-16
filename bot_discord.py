import discord
from discord.ext import commands
import yt_dlp
import asyncio
import random
import re

TOKEN = 'SEU_TOKEN_AQUI'

# Intents necessários para o bot funcionar corretamente
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Variável para armazenar o estado do loop
looping = False

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command()
async def join(ctx):
    """Comando para o bot entrar no canal de voz do usuário."""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.move_to(channel)
    else:
        await ctx.send("Você precisa estar em um canal de voz para eu entrar!")

@bot.command()
async def leave(ctx):
    """Comando para o bot sair do canal de voz."""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.send("Não estou em nenhum canal de voz!")

@bot.command()
async def play(ctx, url):
    """Comando para tocar uma música a partir de um link do YouTube."""
    global looping

    if not ctx.voice_client:
        await ctx.invoke(join)

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        'extract_flat': False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
        title = info['title']

    def after_playing(error):
        if error:
            print(f"Erro: {error}")
        if looping:
            asyncio.run_coroutine_threadsafe(play(ctx, url), bot.loop)


    ctx.voice_client.stop()  # Para qualquer áudio anterior antes de tocar outro
    ctx.voice_client.play(discord.FFmpegPCMAudio(url2), after=after_playing)

    await ctx.send(f"🎶 Tocando agora: **{title}**")

@bot.command()
async def stop(ctx):
    """Comando para parar a música."""
    global looping
    looping = False  # Desliga o loop ao parar a música

    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏹️ Música parada.")
        await ctx.invoke(leave)
    else:
        await ctx.send("Não estou tocando nenhuma música no momento.")

@bot.command()
async def loop(ctx):
    """Comando para ativar o loop da música."""
    global looping

    looping = not looping
    await ctx.send(f"🔁 Loop {'ativado' if looping else 'desativado'}.")


@bot.command()
async def roll(ctx, *, dice_expression: str):
    """
    Rola várias quantidades de dados de diferentes lados e realiza operações matemáticas.
    Exemplo de uso: !roll 1d8 - 3d6 + 5 - 4
    """
    try:
        # Expressão regular para encontrar padrões do tipo XdY, números fixos e operadores
        pattern = re.compile(r'(\d+d\d+)|(\d+)|([+-])')
        matches = pattern.findall(dice_expression)
        
        total = 0
        results = []
        current_operator = '+'  # Começa com soma por padrão
        
        for match in matches:
            dice, fixed, operator = match
            
            if operator:
                # Atualiza o operador atual
                current_operator = operator
            
            elif dice:
                # Processa rolagens de dados
                amount, sides = map(int, dice.lower().split('d'))
                
                # Limita a quantidade e o número de lados para evitar abusos
                if amount <= 0 or sides <= 0:
                    await ctx.send("🚫 A quantidade e o número de lados devem ser maiores que zero.")
                    return
                if amount > 100:
                    await ctx.send("🚫 Não posso rolar mais de 100 dados de uma vez!")
                    return
                
                # Rola os dados e armazena os resultados
                dice_results = [random.randint(1, sides) for _ in range(amount)]
                sum_dice = sum(dice_results)
                
                # Aplica o operador atual
                if current_operator == '+':
                    total += sum_dice
                elif current_operator == '-':
                    total -= sum_dice
                
                results.append(f"**{dice}**: {', '.join(map(str, dice_results))}")
            
            elif fixed:
                # Processa valores fixos
                value = int(fixed)
                
                # Aplica o operador atual
                if current_operator == '+':
                    total += value
                elif current_operator == '-':
                    total -= value
                
                results.append(f"**{fixed}**")
        
        # Formata a mensagem com quebras de linha após cada rolagem
        formatted_results = "\n".join(results)
        
        # Mensagem de resposta com os resultados e o total
        await ctx.send(f"🎲 Rolando **{dice_expression}**:\n{formatted_results}\n(Total: **{total}**)")

    except Exception as e:
        await ctx.send(f"❗ Ocorreu um erro: {e}. Use o formato correto, por exemplo: `!roll 1d8 - 3d6 + 5 - 4`")

@bot.command()
async def help(ctx):
    """Comando para mostrar a lista de comandos disponíveis."""
    help_text = (
        "**Aqui estão os comandos disponíveis:**\n"
        "\n🔹 **!help** -> Mostra esta lista de comandos."
        "\n🔹 **!roll XdY** -> Rola X dados de Y lados."
        "\n🔹 **!play <link_do_Youtube>** -> Toco uma música do Youtube."
        "\n🔹 **!stop** -> Paro a música do Youtube."
        "\n🔹 **!loop** -> Ativo/desativo o modo de repetição da música do Youtube."
    )
    await ctx.send(help_text)


bot.run(TOKEN)
