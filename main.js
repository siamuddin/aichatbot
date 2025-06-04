const { Client, GatewayIntentBits } = require('discord.js');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const express = require('express');

// Create Express app for Render
const app = express();
const PORT = process.env.PORT || 3000;

// Basic route for health check
app.get('/', (req, res) => {
    res.send('Discord Bot is running!');
});

// Start Express server
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

// Initialize Discord client
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
    ],
});

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-pro" });

// Bot ready event
client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
});

// Message handler
client.on('messageCreate', async (message) => {
    // Ignore messages from bots
    if (message.author.bot) return;

    // Only respond to messages that mention the bot or are DMs
    if (!message.mentions.has(client.user) && message.guild) return;

    try {
        // Show typing indicator
        await message.channel.sendTyping();

        // Get the message content and remove bot mention
        let prompt = message.content.replace(`<@${client.user.id}>`, '').trim();
        
        // If no prompt after removing mention, provide a default
        if (!prompt) {
            prompt = "Hello! How can I help you today?";
        }

        // Generate response using Gemini
        const result = await model.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        // Discord has a 2000 character limit for messages
        if (text.length > 2000) {
            // Split long messages
            const chunks = text.match(/.{1,1900}/g);
            for (const chunk of chunks) {
                await message.reply(chunk);
            }
        } else {
            await message.reply(text);
        }

    } catch (error) {
        console.error('Error generating response:', error);
        await message.reply('Sorry, I encountered an error while processing your request. Please try again later.');
    }
});

// Error handling
client.on('error', console.error);

// Login to Discord
client.login(process.env.DISCORD_TOKEN);
