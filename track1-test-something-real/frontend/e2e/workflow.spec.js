import { test, expect } from '@playwright/test';

async function load(page){
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Revenue intelligence.'})).toBeVisible();
 await expect(page.getByText('SAMPLE DATA',{exact:false})).toBeVisible();
}

test('both workspaces, validation, audit, relationships and scenario',async({page})=>{
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await load(page);
 await page.getByRole('button',{name:/Experiment lab/}).click();
 await page.getByRole('button',{name:'Preview B · Decision'}).click();
 await expect(page.getByText('TODAY’S DECISION BRIEF')).toBeVisible();
 await page.reload();await expect(page.getByText('TODAY’S DECISION BRIEF')).toBeVisible();
 await page.getByRole('button',{name:'Review action',exact:true}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.getByLabel('Review note').fill('Verify balance and contact the account owner after invoice review.');
 await page.getByRole('button',{name:'Approve & record task'}).click();
 await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.getByRole('button',{name:/Action log/}).first().click();
 await expect(page.getByText('Verify balance and contact the account owner after invoice review.',{exact:false})).toBeVisible();
 await page.getByRole('button',{name:'Relationships',exact:true}).click();
 await expect(page.getByRole('heading',{name:'The business, connected'})).toBeVisible();
 await page.getByRole('button',{name:'Scenarios',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Illustrative 30-day cash distribution'})).toBeVisible();
 await page.getByRole('button',{name:/Experiment lab/}).click();
 await page.getByRole('button',{name:'Preview A · Standard'}).click();
 await expect(page.getByRole('heading',{name:'Invoice register'})).toBeVisible();
 await expect(page.getByText('TODAY’S DECISION BRIEF')).toHaveCount(0);
 expect(errors).toEqual([]);
});

test('search, real CSV import, scenario values and export',async({page})=>{
 await load(page);
 await page.getByLabel('Search invoices').fill('Northstar');
 await expect(page.locator('tbody tr')).toHaveCount(2);
 await page.getByRole('button',{name:'Import data',exact:true}).click();
 await page.locator('input[type=file]').setInputFiles({name:'invoices.csv',mimeType:'text/csv',buffer:Buffer.from('invoice_id,customer,amount,currency,due_date,status\nREAL-1,Test Enterprise,12345.67,USD,2026-11-01,open\n')});
 await expect(page.getByRole('dialog')).toHaveCount(0);
 await expect(page.getByText('Imported portfolio',{exact:true})).toBeVisible();
 await page.getByLabel('Search invoices').fill('');
 await expect(page.locator('tbody tr')).toHaveCount(1);
 await page.getByRole('button',{name:'Scenarios',exact:true}).click();
 await expect(page.locator('.scenario-baseline').getByText('$12,346',{exact:true})).toBeVisible();
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Export',exact:true}).click();
 expect((await download).suggestedFilename()).toBe('atlas-receivables.csv');
});

for(const width of [375,768,1440]){
 test(`responsive layout ${width}px`,async({page})=>{
  await page.setViewportSize({width,height:1000});await load(page);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path:`../artifacts/atlas-${width}.png`,fullPage:true});
  await page.getByRole('button',{name:'Import data',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible(); await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
 });
}
