const express = require('express');
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const app = express();
// Increase body size limit to handle base64 images
app.use(express.json({ limit: '50mb' })); 

// Initialize WhatsApp Client (saves session locally so you don't have to scan QR every time)
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', (qr) => {
    console.log('\n======================================================');
    console.log('Silakan SCAN QR Code di bawah ini menggunakan WhatsApp:');
    console.log('======================================================\n');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('\n[SUCCESS] WhatsApp Web Bot siap digunakan!');
    console.log('Server berjalan di port 8080...');
});

client.on('auth_failure', msg => {
    console.error('AUTHENTICATION FAILURE', msg);
});

// Endpoint untuk mengirim Teks
app.post('/message/sendText', async (req, res) => {
    try {
        const { number, text } = req.body;
        if (!number || !text) {
            return res.status(400).json({ error: 'Parameter number dan text wajib diisi.' });
        }

        // whatsapp-web.js format format nomor: 628xxx@c.us (untuk nomor pribadi) atau @g.us (grup)
        const chatId = number.includes('@') ? number : `${number}@c.us`;
        
        await client.sendMessage(chatId, text);
        console.log(`[TEXT] Pesan berhasil dikirim ke: ${chatId}`);
        res.status(200).json({ success: true, message: 'Message sent successfully.' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.toString() });
    }
});

// Endpoint untuk mengirim Gambar (Base64)
app.post('/message/sendMedia', async (req, res) => {
    try {
        const { number, caption, media, mimetype } = req.body;
        if (!number || !media) {
            return res.status(400).json({ error: 'Parameter number dan media wajib diisi.' });
        }

        const chatId = number.includes('@') ? number : `${number}@c.us`;
        
        // Buat objek media dari base64
        const mediaFile = new MessageMedia(mimetype || 'image/png', media, 'image.png');
        
        await client.sendMessage(chatId, mediaFile, { caption: caption || '' });
        console.log(`[MEDIA] Gambar berhasil dikirim ke: ${chatId}`);
        res.status(200).json({ success: true, message: 'Media sent successfully.' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: err.toString() });
    }
});

client.initialize();
app.listen(8080, () => {
    console.log('Menjalankan Inisialisasi WhatsApp (Mohon tunggu sebentar...)');
});
