/**
 * YouTube Empire Discord Bot
 *
 * Mirrors the agent feed to Discord channels, forwards escalations,
 * and lets Pedro command agents directly from Discord.
 *
 * Setup:
 * 1. Create a Discord bot at https://discord.com/developers/applications
 * 2. Enable Message Content Intent + Server Members Intent
 * 3. Invite bot to your server with permissions: Send Messages, Manage Channels, Embed Links, Read Message History
 * 4. Set env vars: DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, API_URL
 * 5. Run: npm start
 *
 * The bot will auto-create channels matching your feed channels on first run.
 */

const { Client, GatewayIntentBits, EmbedBuilder, ChannelType, PermissionsBitField } = require("discord.js");

// Config
const DISCORD_BOT_TOKEN = process.env.DISCORD_BOT_TOKEN || "";
const DISCORD_GUILD_ID = process.env.DISCORD_GUILD_ID || "";
const API_URL = process.env.API_URL || "http://localhost:8000";
const POLL_INTERVAL = 15000; // 15 seconds
const PEDRO_DISCORD_ID = process.env.PEDRO_DISCORD_ID || ""; // Your Discord user ID for @mentions

if (!DISCORD_BOT_TOKEN) {
  console.error("DISCORD_BOT_TOKEN not set. Add it to your .env file.");
  process.exit(1);
}

// Feed channel → Discord channel mapping
const CHANNEL_CONFIG = {
  general:      { name: "empire-general",    emoji: "💬", color: 0x6366f1, desc: "Company-wide agent updates" },
  content:      { name: "empire-content",    emoji: "📝", color: 0x3b82f6, desc: "Scripts, topics, publishing updates" },
  operations:   { name: "empire-ops",        emoji: "⚙️", color: 0xf59e0b, desc: "Pipeline, production, QA" },
  analytics:    { name: "empire-analytics",  emoji: "📊", color: 0x10b981, desc: "Metrics, trends, performance" },
  monetization: { name: "empire-revenue",    emoji: "💰", color: 0xef4444, desc: "Deals, affiliates, products" },
  alerts:       { name: "empire-alerts",     emoji: "🚨", color: 0xff0000, desc: "Urgent — needs Pedro's attention" },
  wins:         { name: "empire-wins",       emoji: "🏆", color: 0xfbbf24, desc: "Milestones and celebrations" },
};

// Agent name → persona mapping (matches dashboard)
const AGENT_PERSONAS = {
  "ceo-agent": "Marcus Chen",
  "content-vp-agent": "Sofia Rivera",
  "operations-vp-agent": "James Okafor",
  "analytics-vp-agent": "Priya Sharma",
  "monetization-vp-agent": "Daniel Kim",
  "scriptwriter-agent": "Noah Thompson",
  "hook-specialist-agent": "Mia Jackson",
  "seo-specialist-agent": "Ethan Park",
  "data-analyst-agent": "Chloe Williams",
  "trend-researcher-agent": "Leo Martinez",
  "newsletter-strategist-agent": "Sarah Lindgren",
  "qa-lead-agent": "Hannah Lee",
  "secretary-agent": "Emma Fischer",
  "compliance-officer-agent": "David Reeves",
  "project-manager-agent": "Olivia Bennett",
  "web-designer-agent": "Luna Chang",
  "web-developer-agent": "Alex Petrov",
  "reflection-council-agent": "Victor Andrei",
};

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

// Track Discord channel IDs
const discordChannels = {};
let lastPollTime = new Date().toISOString();
let categoryId = null;

// ========== SETUP ==========

async function setupChannels(guild) {
  // Create "YOUTUBE EMPIRE" category if it doesn't exist
  let category = guild.channels.cache.find(
    (c) => c.type === ChannelType.GuildCategory && c.name === "YOUTUBE EMPIRE"
  );
  if (!category) {
    category = await guild.channels.create({
      name: "YOUTUBE EMPIRE",
      type: ChannelType.GuildCategory,
    });
    console.log("Created category: YOUTUBE EMPIRE");
  }
  categoryId = category.id;

  // Create each feed channel
  for (const [feedKey, config] of Object.entries(CHANNEL_CONFIG)) {
    let channel = guild.channels.cache.find(
      (c) => c.name === config.name && c.parentId === category.id
    );
    if (!channel) {
      channel = await guild.channels.create({
        name: config.name,
        type: ChannelType.GuildText,
        parent: category.id,
        topic: `${config.emoji} ${config.desc}`,
      });
      console.log(`Created channel: #${config.name}`);
    }
    discordChannels[feedKey] = channel.id;
  }

  console.log("Discord channels ready:", Object.keys(discordChannels).join(", "));
}

// ========== FEED POLLING ==========

async function pollFeed() {
  try {
    const res = await fetch(`${API_URL}/api/feed/messages?limit=20`);
    if (!res.ok) return;
    const messages = await res.json();

    // Filter to only new messages since last poll
    const newMessages = messages.filter(
      (m) => new Date(m.created_at) > new Date(lastPollTime)
    );

    if (newMessages.length === 0) return;

    // Post newest messages (reversed to chronological order)
    for (const msg of newMessages.reverse()) {
      const channelId = discordChannels[msg.channel] || discordChannels.general;
      if (!channelId) continue;

      const channel = await client.channels.fetch(channelId).catch(() => null);
      if (!channel) continue;

      const config = CHANNEL_CONFIG[msg.channel] || CHANNEL_CONFIG.general;
      const humanName = AGENT_PERSONAS[msg.agent_id] || msg.agent_name;

      const embed = new EmbedBuilder()
        .setColor(config.color)
        .setAuthor({ name: `${humanName} (${msg.agent_name})` })
        .setDescription(msg.content.slice(0, 4000))
        .setTimestamp(new Date(msg.created_at))
        .setFooter({ text: `${config.emoji} ${msg.message_type} • ${msg.channel}` });

      // Severity styling
      if (msg.severity === "urgent") {
        embed.setColor(0xff0000);
        const mentionText = PEDRO_DISCORD_ID ? `<@${PEDRO_DISCORD_ID}> ` : "";
        await channel.send({ content: `${mentionText}🚨 **URGENT — Needs your attention**`, embeds: [embed] });
      } else if (msg.severity === "celebration") {
        embed.setColor(0xfbbf24);
        await channel.send({ content: "🏆 **Win!**", embeds: [embed] });
      } else {
        await channel.send({ embeds: [embed] });
      }

      // Also mark as read in the dashboard
      await fetch(`${API_URL}/api/feed/messages/${msg.id}/read`, { method: "POST" }).catch(() => {});
    }

    lastPollTime = new Date().toISOString();
  } catch (err) {
    console.error("Feed poll error:", err.message);
  }
}

// ========== ESCALATION POLLING ==========

async function pollEscalations() {
  try {
    const res = await fetch(`${API_URL}/api/scheduler/escalations`);
    if (!res.ok) return;
    const escalations = await res.json();

    const pending = escalations.filter((e) => e.status === "pending");
    if (pending.length === 0) return;

    const alertChannel = await client.channels.fetch(discordChannels.alerts).catch(() => null);
    if (!alertChannel) return;

    // Only post new escalations (check by ID to avoid duplicates)
    for (const esc of pending) {
      // Simple dedup: check recent messages in channel
      const recent = await alertChannel.messages.fetch({ limit: 20 });
      const alreadyPosted = recent.some((m) => m.embeds?.[0]?.footer?.text?.includes(esc.id));
      if (alreadyPosted) continue;

      const humanName = AGENT_PERSONAS[esc.agent_id] || esc.agent_name;
      const mentionText = PEDRO_DISCORD_ID ? `<@${PEDRO_DISCORD_ID}>` : "@here";

      const embed = new EmbedBuilder()
        .setColor(esc.severity === "critical" ? 0xff0000 : esc.severity === "high" ? 0xff6600 : 0xffaa00)
        .setTitle(`${esc.severity === "critical" ? "🔴" : "🟡"} Escalation — ${esc.severity.toUpperCase()}`)
        .setAuthor({ name: humanName })
        .setDescription(esc.reason)
        .addFields(
          { name: "Agent", value: esc.agent_name || esc.agent_id, inline: true },
          { name: "Severity", value: esc.severity, inline: true },
        )
        .setTimestamp(new Date(esc.created_at))
        .setFooter({ text: `ID: ${esc.id}` });

      await alertChannel.send({
        content: `${mentionText} — Escalation from your team`,
        embeds: [embed],
      });
    }
  } catch (err) {
    console.error("Escalation poll error:", err.message);
  }
}

// ========== COMMAND HANDLING ==========

client.on("messageCreate", async (message) => {
  if (message.author.bot) return;

  // Only respond in empire channels
  const isEmpireChannel = Object.values(discordChannels).includes(message.channelId);
  if (!isEmpireChannel) return;

  const content = message.content.trim();

  // !status — get workforce status
  if (content === "!status") {
    try {
      const res = await fetch(`${API_URL}/api/scheduler/activity`);
      const data = await res.json();
      const working = data.agent_statuses.filter((a) => a.status === "working");

      const embed = new EmbedBuilder()
        .setColor(0x8b5cf6)
        .setTitle("📊 Workforce Status")
        .addFields(
          { name: "Running Now", value: `${data.running_count}`, inline: true },
          { name: "Completed Today", value: `${data.completed_today}`, inline: true },
          { name: "Escalations", value: `${data.pending_escalations}`, inline: true },
          { name: "Total Agents", value: `${data.total_agents}`, inline: true },
        )
        .setTimestamp();

      if (working.length > 0) {
        embed.addFields({
          name: "Currently Working",
          value: working.map((a) => `• **${AGENT_PERSONAS[a.id] || a.name}** — ${a.current_task}`).join("\n"),
        });
      }

      await message.reply({ embeds: [embed] });
    } catch {
      await message.reply("Could not fetch status. Is the backend running?");
    }
    return;
  }

  // !tasks — list scheduled tasks
  if (content === "!tasks") {
    try {
      const res = await fetch(`${API_URL}/api/scheduler/tasks`);
      const tasks = await res.json();
      const enabled = tasks.filter((t) => t.enabled);

      const embed = new EmbedBuilder()
        .setColor(0x3b82f6)
        .setTitle(`⏰ Scheduled Tasks (${enabled.length} active)`)
        .setDescription(
          enabled
            .slice(0, 20)
            .map((t) => `\`${t.cron_expression}\` **${t.name}** — ${AGENT_PERSONAS[t.agent_id] || t.agent_name}`)
            .join("\n")
        )
        .setTimestamp();

      await message.reply({ embeds: [embed] });
    } catch {
      await message.reply("Could not fetch tasks.");
    }
    return;
  }

  // !run <task name> — manually trigger a task
  if (content.startsWith("!run ")) {
    const taskName = content.slice(5).trim().toLowerCase();
    try {
      const res = await fetch(`${API_URL}/api/scheduler/tasks`);
      const tasks = await res.json();
      const match = tasks.find((t) => t.name.toLowerCase().includes(taskName));
      if (!match) {
        await message.reply(`No task found matching "${taskName}". Use \`!tasks\` to see available tasks.`);
        return;
      }
      await fetch(`${API_URL}/api/scheduler/tasks/${match.id}/run`, { method: "POST" });
      await message.reply(`✅ Triggered: **${match.name}** → ${AGENT_PERSONAS[match.agent_id] || match.agent_name}`);
    } catch {
      await message.reply("Failed to trigger task.");
    }
    return;
  }

  // !resolve <escalation-id> — resolve an escalation
  if (content.startsWith("!resolve ")) {
    const escId = content.slice(9).trim();
    try {
      await fetch(`${API_URL}/api/scheduler/escalations/${escId}/resolve`, { method: "POST" });
      await message.reply(`✅ Escalation resolved: ${escId}`);
    } catch {
      await message.reply("Failed to resolve. Check the ID.");
    }
    return;
  }

  // !pipeline — show production pipeline
  if (content === "!pipeline") {
    try {
      const res = await fetch(`${API_URL}/api/production/jobs`);
      const jobs = await res.json();
      if (jobs.length === 0) {
        await message.reply("No active production jobs.");
        return;
      }

      const stageEmojis = {
        research: "🔍", scripted: "📝", voiceover: "🎙️", thumbnail: "🖼️",
        edited: "🎬", seo: "🔎", review: "✅", approved: "👍", published: "📺",
      };

      const embed = new EmbedBuilder()
        .setColor(0x10b981)
        .setTitle(`🎬 Production Pipeline (${jobs.length} jobs)`)
        .setDescription(
          jobs
            .slice(0, 15)
            .map((j) => `${stageEmojis[j.stage] || "⏳"} **${j.title}** (${j.channel}) — \`${j.stage}\`${j.current_agent_name ? ` → ${j.current_agent_name}` : ""}`)
            .join("\n")
        )
        .setTimestamp();

      await message.reply({ embeds: [embed] });
    } catch {
      await message.reply("Could not fetch pipeline.");
    }
    return;
  }

  // !agents — list all agents
  if (content === "!agents") {
    try {
      const res = await fetch(`${API_URL}/api/agents`);
      const agents = await res.json();

      const byDept = {};
      agents.forEach((a) => {
        if (!byDept[a.department]) byDept[a.department] = [];
        byDept[a.department].push(a);
      });

      const embed = new EmbedBuilder()
        .setColor(0x8b5cf6)
        .setTitle(`👥 Agent Roster (${agents.length})`)
        .setTimestamp();

      for (const [dept, deptAgents] of Object.entries(byDept)) {
        embed.addFields({
          name: dept.charAt(0).toUpperCase() + dept.slice(1),
          value: deptAgents.map((a) => `• **${AGENT_PERSONAS[a.id] || a.name}** — ${a.role}`).join("\n"),
          inline: false,
        });
      }

      await message.reply({ embeds: [embed] });
    } catch {
      await message.reply("Could not fetch agents.");
    }
    return;
  }

  // !ask <message> — send a task to the CEO agent
  if (content.startsWith("!ask ")) {
    const task = content.slice(5).trim();
    if (!task) {
      await message.reply("Usage: `!ask <your task or question>`");
      return;
    }

    await message.reply(`📤 Sending to CEO (Marcus Chen)...`);

    try {
      const agentsRes = await fetch(`${API_URL}/api/agents`);
      const agents = await agentsRes.json();
      const ceo = agents.find((a) => a.id.includes("ceo"));

      const threadRes = await fetch(`${API_URL}/api/threads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: task.slice(0, 60),
          recipient_agent_ids: [ceo?.id || "ceo-agent"],
          content: task,
        }),
      });
      const thread = await threadRes.json();

      // Wait for response
      await new Promise((r) => setTimeout(r, 10000));

      const fullThread = await fetch(`${API_URL}/api/threads/${thread.id}`).then((r) => r.json());
      const agentMsgs = fullThread.messages?.filter((m) => m.sender_type === "agent") || [];

      if (agentMsgs.length > 0) {
        for (const agentMsg of agentMsgs.slice(0, 3)) {
          const humanName = AGENT_PERSONAS[agentMsg.sender_agent_id] || agentMsg.sender_name || "Agent";
          const embed = new EmbedBuilder()
            .setColor(0x8b5cf6)
            .setAuthor({ name: humanName })
            .setDescription(agentMsg.content.slice(0, 4000))
            .setTimestamp();
          await message.channel.send({ embeds: [embed] });
        }
      } else {
        await message.reply("Agents are processing... check the dashboard for updates.");
      }
    } catch (err) {
      await message.reply(`Error: ${err.message}`);
    }
    return;
  }

  // !help — show commands
  if (content === "!help") {
    const embed = new EmbedBuilder()
      .setColor(0x8b5cf6)
      .setTitle("🤖 YouTube Empire Bot — Commands")
      .setDescription("Control your 32-agent workforce from Discord")
      .addFields(
        { name: "`!status`", value: "Workforce status — who's working, completions, escalations", inline: false },
        { name: "`!agents`", value: "List all agents by department", inline: false },
        { name: "`!tasks`", value: "List all scheduled tasks", inline: false },
        { name: "`!run <name>`", value: "Trigger a task manually (e.g. `!run trend scan`)", inline: false },
        { name: "`!pipeline`", value: "Show production pipeline status", inline: false },
        { name: "`!ask <message>`", value: "Send a task to the CEO — agents will respond", inline: false },
        { name: "`!resolve <id>`", value: "Resolve an escalation by ID", inline: false },
        { name: "`!help`", value: "Show this help", inline: false },
      )
      .setFooter({ text: "YouTube Empire — Goal: 1B Subscribers" });

    await message.reply({ embeds: [embed] });
    return;
  }
});

// ========== STARTUP ==========

client.once("ready", async () => {
  console.log(`Discord bot logged in as ${client.user.tag}`);

  const guild = await client.guilds.fetch(DISCORD_GUILD_ID).catch(() => null);
  if (!guild) {
    console.error(`Could not find guild ${DISCORD_GUILD_ID}. Check DISCORD_GUILD_ID.`);
    return;
  }

  await setupChannels(guild);

  // Start polling
  setInterval(pollFeed, POLL_INTERVAL);
  setInterval(pollEscalations, POLL_INTERVAL * 2);
  console.log(`Polling feed every ${POLL_INTERVAL / 1000}s`);

  // Post startup message
  const generalChannel = await client.channels.fetch(discordChannels.general).catch(() => null);
  if (generalChannel) {
    const embed = new EmbedBuilder()
      .setColor(0x10b981)
      .setTitle("🟢 YouTube Empire Online")
      .setDescription("32 agents deployed and autonomous. All systems operational.\n\nType `!help` for commands.")
      .setTimestamp();
    await generalChannel.send({ embeds: [embed] });
  }
});

client.login(DISCORD_BOT_TOKEN);
