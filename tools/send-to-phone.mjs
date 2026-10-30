// Sends the built ROM to Kyle's iPhone over PairDrop (https://pairdrop.net).
//
//   node tools/send-to-phone.mjs [file.nds]
//
// The browser profile is kept in %LOCALAPPDATA%\pokelegends-pairdrop, so once the phone
// is paired, later sends need no code. If no paired phone is online, this opens PairDrop's
// "Pair device" dialog and prints its 6-digit code: type it on the iPhone in
// pairdrop.net > Pair device. PairDrop must be open on the phone.

import { chromium } from 'playwright';
import { existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

const file = resolve(process.argv[2] ?? 'PokeLegendsofNine-DS.nds');
const profile = join(process.env.LOCALAPPDATA ?? '.', 'pokelegends-pairdrop');

function fail(msg) {
    console.error(`send-to-phone: ${msg}`);
    process.exit(1);
}

if (!existsSync(file)) fail(`${file} not found. Run make first.`);

const context = await chromium.launchPersistentContext(profile, { headless: !process.env.HEADED });
const page = context.pages()[0] ?? await context.newPage();
// A paired device shows up as an x-peer in the "secret" room.
const peer = page.locator('x-peer.type-secret').first();

try {
    await page.goto('https://pairdrop.net/');

    const paired = await peer.waitFor({ state: 'attached', timeout: 10_000 }).then(() => true, () => false);
    if (!paired) {
        await page.click('#pair-device');
        const key = page.locator('#pair-device-dialog .key');
        await page.waitForFunction(el => !el.textContent.includes('000 000'), await key.elementHandle(),
            { timeout: 30_000 }).catch(() => fail('PairDrop did not show a pair code.'));
        console.log(`PAIR CODE: ${(await key.innerText()).trim()}`);
        console.log('On the iPhone: pairdrop.net > Pair device > enter this code. Waiting 5 minutes...');
        await peer.waitFor({ state: 'attached', timeout: 300_000 })
            .catch(() => fail('the phone did not pair within 5 minutes. Run again for a new code.'));
    }

    console.log(`Sending ${file} to ${await peer.locator('.name').innerText()}...`);
    await peer.locator('input[type="file"]').setInputFiles(file);

    // The peer gets a status attribute while the transfer runs, and loses it when done.
    const el = await peer.elementHandle();
    await page.waitForFunction(e => e.hasAttribute('status'), el, { timeout: 30_000 }).catch(() => {});
    await page.waitForFunction(e => !e.hasAttribute('status'), el, { timeout: 180_000 })
        .catch(() => fail('the transfer did not finish in 3 minutes. Accept it on the phone and try again.'));
    console.log('Sent. On the iPhone: save it to Files, then share it to Delta.');
} finally {
    await context.close();
}
