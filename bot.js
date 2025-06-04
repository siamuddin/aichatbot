const { Client, GatewayIntentBits } = require('discord.js');
const axios = require('axios');

// Create Discord client
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
});

// Configuration - these will be set as environment variables
const DISCORD_TOKEN = process.env.DISCORD_TOKEN;
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const BOT_PREFIX = '!'; // Users will type !ask to talk to the bot

// Function to get AI response from OpenRouter
async function getAIResponse(message) {
    try {
        const response = await axios.post(
            'https://openrouter.ai/api/v1/chat/completions',
            {
                model: 'anthropic/claude-3-haiku', // You can change this model
                messages: [
                    {
                        role: 'user',
                        content: message
                    }
                ],
                max_tokens: 500, // Adjust as needed
            },
            {
                headers: {
                    'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
                    'Content-Type': 'application/json',
                },
            }
        );

        return response.data.choices[0].message.content;
    } catch (error) {
        console.error('Error calling OpenRouter API:', error.response?.data || error.message);
        return 'Sorry, I encountered an error processing your request.';
    }
}

// Bot ready event
client.once('ready', () => {
    console.log(`Bot is online as ${client.user.tag}!`);
});

// Message handling
client.on('messageCreate', async (message) => {
    // Ignore messages from bots
    if (message.author.bot) return;

    // Check if message starts with prefix
    if (!message.content.startsWith(BOT_PREFIX)) return;

    // Extract command and content
    const args = message.content.slice(BOT_PREFIX.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    // Handle different commands
    if (command === 'ask') {
        const question = args.join(' ');
        
        if (!question) {
            message.reply('Please provide a question! Example: `!ask What is the weather like?`');
            return;
        }

        // Show typing indicator
        message.channel.sendTyping();

        try {
            const aiResponse = await getAIResponse(question);
            
            // Discord has a 2000 character limit, so split long messages
            if (aiResponse.length <= 2000) {
                message.reply(aiResponse);
            } else {
                // Split into chunks
                const chunks = aiResponse.match(/.{1,1900}/g) || [];
                for (let i = 0; i < chunks.length; i++) {
                    if (i === 0) {
                        message.reply(chunks[i]);
                    } else {
                        message.channel.send(chunks[i]);
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            message.reply('Sorry, something went wrong while processing your request.');
        }
    }
    
    // Help command
    else if (command === 'help') {
        const helpMessage = `
**🤖 Bot Commands:**
\`!ask [question]\` - Ask me anything!
\`!help\` - Show this help message

**Examples:**
\`!ask What is artificial intelligence?\`
\`!ask Tell me a joke\`
\`!ask Explain quantum physics simply\`
        `;
        message.reply(helpMessage);
    }
});

// Error handling
client.on('error', error => {
    console.error('Discord client error:', error);
});

process.on('unhandledRejection', error => {
    console.error('Unhandled promise rejection:', error);
});

// Login to Discord
client.login(DISCORD_TOKEN);
