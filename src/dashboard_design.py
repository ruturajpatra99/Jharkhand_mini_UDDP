"""Readable presentation layer for the existing, validated Excel dashboard.

No data cleaning or scoring occurs here. All figures link to existing CSV-backed
worksheets. Ranked snapshot lists are rebuilt whenever the pipeline runs.
"""
from __future__ import annotations
from copy import copy
from datetime import datetime
from zoneinfo import ZoneInfo
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.data_source import StrRef
from openpyxl.chart.series import DataPoint, SeriesLabel
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

NAVY='18334F'; INK='22354A'; MUTED='52667A'; BLUE='2364AA'
BG='F3F6FA'; WHITE='FFFFFF'; LINE='DEE6EF'
RED='B42332'; AMBER='9A6500'; GREEN='217148'
TINTS={'High':'FCE9EB','Medium':'FFF4CF','Low':'E6F3E9'}
ACCENTS={'High':RED,'Medium':AMBER,'Low':GREEN}
ANALYSIS='District Analysis'


def fill(ws,r1,c1,r2,c2,color):
    for row in ws.iter_rows(min_row=r1,max_row=r2,min_col=c1,max_col=c2):
        for c in row:c.fill=PatternFill('solid',fgColor=color)


def block(ws,r,c1,c2,text,*,size=11,bold=False,color=INK,bg=None,height=None,align='left',end=None):
    end=end or r
    ws.merge_cells(start_row=r,start_column=c1,end_row=end,end_column=c2)
    cell=ws.cell(r,c1,text);cell.font=Font(name='Calibri',size=size,bold=bold,color=color)
    cell.alignment=Alignment(horizontal=align,vertical='center',wrap_text=True,indent=1 if align=='left' else 0)
    if bg:fill(ws,r,c1,end,c2,bg)
    if height:ws.row_dimensions[r].height=height
    return cell


def canvas(ws,last=60):
    ws.sheet_view.showGridLines=False;ws.sheet_view.zoomScale=85
    ws.column_dimensions['A'].width=2.5;ws.column_dimensions['N'].width=2.5
    for c in range(2,14):ws.column_dimensions[L(c)].width=10.5
    for r in range(1,last+1):ws.row_dimensions[r].height=21
    fill(ws,1,1,last,14,BG)
    ws.sheet_properties.pageSetUpPr.fitToPage=True
    ws.page_setup.paperSize=ws.PAPERSIZE_A3;ws.page_setup.orientation='portrait'
    ws.page_setup.fitToWidth=1;ws.page_setup.fitToHeight=1
    ws.print_options.horizontalCentered=True
    ws.page_margins.left=.2;ws.page_margins.right=.2;ws.page_margins.top=.25;ws.page_margins.bottom=.25
    ws.oddFooter.center.text='Jharkhand Mini-UDDP | Estimated aggregate data'
    ws.oddFooter.right.text='Page &P of &N'
    ws.freeze_panes='B12'


def link(ws,r,c1,c2,text,target):
    cell=block(ws,r,c1,c2,text,size=10,bold=True,color=BLUE,bg=WHITE,height=27,align='center')
    cell.hyperlink=f"#'{target}'!A1"


def card(ws,c1,c2,label,formula,caption,*,color=BLUE,tint='E8F0FA',fmt='#,##0'):
    fill(ws,6,c1,9,c2,WHITE)
    block(ws,6,c1,c2,label,size=10,bold=True,color=color,bg=tint,height=25,align='center')
    v=block(ws,7,c1,c2,formula,size=25,bold=True,color=color,bg=WHITE,end=8,align='center');v.number_format=fmt
    block(ws,9,c1,c2,caption,size=9,color=MUTED,bg=WHITE,height=25,align='center')
    # White separators distinguish adjacent cards without oversized gutters.
    for r in range(6,10):
        ws.cell(r,c1).border=Border(left=Side(style='medium',color=BG))
        ws.cell(r,c2).border=Border(right=Side(style='medium',color=BG))


def apply_readable_design(wb,profile,headers,mart,run_id):
    """Reflow the existing dashboard while retaining inputs, charts and selectors."""
    ws=wb['Executive Dashboard'];charts=list(ws._charts)
    # Keep hidden chart-helper formulas O:W and all three CSV-backed tabs intact.
    for merged in list(ws.merged_cells.ranges):ws.unmerge_cells(str(merged))
    for row in ws.iter_rows(min_row=1,max_row=90,min_col=1,max_col=14):
        for cell in row:cell.value=None;cell._style=None;cell.hyperlink=None
    ws._charts=[];ws.row_breaks.brk=[]
    canvas(ws,58)
    block(ws,2,2,13,'JHARKHAND | Pension Outreach',size=23,bold=True,color=WHITE,bg=NAVY,height=41,end=3)
    block(ws,4,2,13,'Find districts that need attention first. Explore the evidence, then plan outreach.',size=11,color=MUTED,height=28)
    def rg(col):return f"'Pension Outreach Mart'!${L(headers.index(col)+1)}$2:${L(headers.index(col)+1)}${len(mart)+1}"
    card(ws,2,4,'DISTRICTS IN VIEW',f'=COUNTA({rg("district_code")})','Jharkhand district records')
    card(ws,5,7,'HIGH PRIORITY',f'=SUMPRODUCT(--(UPPER(TRIM({rg("priority_category")}))="HIGH"))','Start with the list below',color=RED,tint=TINTS['High'])
    card(ws,8,10,'ESTIMATED SCHEME ENTRIES',f'=SUM({rg("old_age_estimated_beneficiaries")},{rg("widow_estimated_beneficiaries")},{rg("disability_estimated_beneficiaries")})','Sum of 3 schemes; people may overlap',color=BLUE)
    card(ws,11,13,'DISTRICTS MATCHED',f'=IFERROR(COUNTIF(\'District Matching Report\'!$H$2:$H${len(mart)+1},"Matched")/B7,0)','Matched across all 3 input sources',color=GREEN,tint=TINTS['Low'],fmt='0%')
    link(ws,11,2,4,'All district data  >','Pension Outreach Mart')
    link(ws,11,5,7,'Compare districts  >','District Comparison')
    link(ws,11,8,10,'Detailed charts  >',ANALYSIS)
    link(ws,11,11,13,'How to read this  >','Dashboard Guide')
    block(ws,13,2,13,'READ FIRST: Red = High priority  |  Yellow = Medium  |  Green = Low. These are relative outreach priorities, not verified eligibility gaps.',size=10,color=INK,bg='E8F0FA',height=34)
    high=[r for r in profile['ranked'] if r['priority_category'].strip().title()=='High']
    block(ws,15,2,13,'01  |  Start here: High Priority districts',size=13,bold=True,color=WHITE,bg=NAVY,height=29)
    specs=[(2,2,'Rank','priority_rank'),(3,5,'District','district_name'),(6,7,'Score / 100','pension_outreach_priority_score'),(8,9,'Old age / 1,000','estimated_old_age_per_1000_population'),(10,11,'Widow / 1,000','estimated_widow_per_1000_population'),(12,13,'Priority','priority_category')]
    for c1,c2,label,_ in specs:block(ws,16,c1,c2,label,size=10,bold=True,color=MUTED,bg='E7EDF4',height=30,align='left' if c1==3 else 'center')
    positions={r['district_code']:i+2 for i,r in enumerate(mart)}
    for row,r in enumerate(high,17):
        for c1,c2,_,col in specs:
            formula=f"='Pension Outreach Mart'!{L(headers.index(col)+1)}{positions[r['district_code']]}"
            cell=block(ws,row,c1,c2,formula,size=11,bold=col in {'district_name','priority_rank','priority_category'},color=RED if col=='priority_category' else INK,bg=TINTS['High'] if row%2 else WHITE,height=27,align='left' if col=='district_name' else 'center')
            cell.number_format='0.0' if 'score' in col or 'per_1000' in col else '0'
    block(ws,25,2,13,'Higher score = higher outreach priority. Old age and widow rates are estimated entries per 1,000 residents; they are not eligible-person coverage.',size=10,color=MUTED,height=32)
    block(ws,27,2,13,'02  |  Understand the priority picture',size=13,bold=True,color=WHITE,bg=NAVY,height=29)
    # Preserve original native chart sources and their formulas.
    pie,bar=charts[0],charts[1]
    pie.title='Districts by priority';pie.width=11.5;pie.height=9.5;pie.holeSize=65;pie.legend.position='b'
    pie.dataLabels=DataLabelList();pie.dataLabels.showVal=True;pie.dataLabels.showPercent=False;pie.dataLabels.dLblPos='bestFit';pie.dataLabels.showCatName=False;pie.dataLabels.showSerName=False;pie.dataLabels.showLegendKey=False
    for i,color in enumerate([RED,'E6AC24',GREEN]):
        dp=DataPoint(idx=i);dp.graphicalProperties.solidFill=color;dp.graphicalProperties.line.solidFill=WHITE
        pie.series[0].data_points[i]=dp
    bar.title='Top 10 districts | score out of 100';bar.width=12.0;bar.height=9.5;bar.y_axis.scaling.min=0;bar.y_axis.scaling.max=100
    bar.dataLabels=DataLabelList();bar.dataLabels.showVal=True;bar.dataLabels.numFmt='0.0';bar.dataLabels.showCatName=False;bar.dataLabels.showSerName=False;bar.dataLabels.showLegendKey=False;bar.dataLabels.showPercent=False;bar.dataLabels.dLblPos='outEnd';bar.legend=None;bar.y_axis.numFmt='0';bar.y_axis.majorUnit=20
    bar.series[0].graphicalProperties.solidFill=RED;bar.series[0].graphicalProperties.line.noFill=True
    bar.series[0].data_points=[]
    for i,r in enumerate(profile['ranked'][:10]):
        dp=DataPoint(idx=i);dp.graphicalProperties.solidFill=ACCENTS[r['priority_category'].strip().title()];bar.series[0].data_points.append(dp)
    ws.add_chart(pie,'B29');ws.add_chart(bar,'H29')
    block(ws,46,2,13,'03  |  Estimated scheme entries',size=13,bold=True,color=WHITE,bg=NAVY,height=29)
    for c1,c2,label,col in [(2,5,'Old age pension','old_age_estimated_beneficiaries'),(6,9,'Widow pension','widow_estimated_beneficiaries'),(10,13,'Disability pension','disability_estimated_beneficiaries')]:
        block(ws,47,c1,c2,label,size=10,bold=True,color=MUTED,bg=WHITE,height=24,align='center')
        cell=block(ws,48,c1,c2,f'=SUM({rg(col)})',size=21,bold=True,color=NAVY,bg=WHITE,height=36,align='center');cell.number_format='#,##0'
    block(ws,50,2,13,'Important: pension numbers are supplied district estimates, not verified observations. Scheme entries may overlap across people. Census demographics are from 2011; pension reference year is unavailable.',size=10,color=MUTED,height=38)
    block(ws,53,2,13,'Next: open All district data to filter High / Medium / Low, or Compare districts to choose two names.',size=10,bold=True,color=BLUE,height=25)
    stamp=datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%d %b %Y, %I:%M %p IST')
    block(ws,55,2,13,f'Generated {stamp}  |  Refresh: run the pipeline  |  Snapshot ID: {run_id[:12]}',size=9,color=MUTED,height=24)
    ws.print_area='A1:N56'
    # Explicit helper-column visibility is also respected by non-Excel viewers.
    ws.column_dimensions['N'].min=14;ws.column_dimensions['N'].max=14;ws.column_dimensions['N'].hidden=False
    for c in range(15,24):ws.column_dimensions[L(c)].hidden=True
    # Longer diagnostics remain available without overwhelming the landing view.
    analysis=wb.create_sheet(ANALYSIS);canvas(analysis,78)
    block(analysis,2,2,13,'District analysis | supporting evidence',size=21,bold=True,color=WHITE,bg=NAVY,height=38,end=3)
    block(analysis,4,2,13,'Use these charts to explore the supplied estimates. No new score or eligibility measure is calculated.',size=11,color=MUTED,height=30)
    link(analysis,6,2,6,'<  Back to overview','Executive Dashboard');link(analysis,6,8,13,'Open district data  >','Pension Outreach Mart')
    for ch,anchor in zip(charts[2:],['B9','B57','H57','B33']):
        ch.width=11.6;ch.height=8.1;ch.visible_cells_only=False;analysis.add_chart(ch,anchor)
    # Long district labels fit more comfortably on horizontal charts.
    for idx in [0,3]:
        ch=analysis._charts[idx];ch.type='bar';ch.x_axis.scaling.orientation='maxMin';ch.y_axis.crosses='max';ch.legend.position='b';ch.width=23.5;ch.height=15
    analysis._charts[0].title='Scheme estimates | all 24 districts'
    analysis._charts[1].title='Population vs priority score'
    analysis._charts[2].title='Matching status | source records'
    analysis._charts[3].title='Pension estimates per 1,000 residents'
    block(analysis,75,2,13,'Charts with 24 districts are best viewed at 100% zoom. For exact values, use the filtered data tables. Matching records = district × source, so 24 matched districts produce 72 records.',size=10,color=MUTED,height=36)
    analysis.print_area='A1:N77';analysis.freeze_panes='B8';analysis.page_setup.fitToHeight=0
    from openpyxl.worksheet.pagebreak import Break
    analysis.row_breaks.append(Break(id=31));analysis.row_breaks.append(Break(id=55))
    _comparison(wb,rg,profile)
    _guide(wb,profile,stamp,run_id)
    for title in ['Pension Outreach Mart','ML District Features']:
        raw=wb[title];raw.sheet_properties.tabColor='879BB0';raw.sheet_view.zoomScale=85
        for col in raw[1]:
            col.font=Font(name='Calibri',size=10,bold=True,color=WHITE)
        raw.sheet_properties.pageSetUpPr.fitToPage=True
    wb['District Matching Report'].sheet_properties.tabColor=GREEN
    ws.sheet_properties.tabColor=BLUE;analysis.sheet_properties.tabColor=BLUE
    wb['District Comparison'].sheet_properties.tabColor='E6AC24';wb['Dashboard Guide'].sheet_properties.tabColor='879BB0'
    wb.active=0


def _comparison(wb,rg,profile):
    old=wb['District Comparison'];validations=old.data_validations
    # Preserve C3/I3 named-range dropdowns while making their hit areas readable.
    for merged in list(old.merged_cells.ranges):old.unmerge_cells(str(merged))
    old.delete_rows(1,old.max_row);old._charts=[];canvas(old,43);old.data_validations=validations
    block(old,1,2,13,'Compare two districts',size=22,bold=True,color=WHITE,bg=NAVY,height=39)
    old['B3']='District A';old['H3']='District B'
    block(old,3,3,6,profile['ranked'][0]['district_name'],size=12,bold=True,color=BLUE,bg='FFF4CF',height=32)
    block(old,3,9,12,profile['ranked'][1]['district_name'],size=12,bold=True,color=BLUE,bg='FFF4CF')
    block(old,4,2,13,'Click each yellow cell and use its dropdown arrow to choose a district. The table and chart update in Excel.',size=10,color=MUTED,height=29)
    link(old,6,2,6,'<  Back to overview','Executive Dashboard')
    metrics=[('Population','population','People'),('Priority score','pension_outreach_priority_score','0–100; higher = higher priority'),('Priority rank','priority_rank','1 = highest priority'),('Priority category','priority_category','Relative priority group'),('Old age pension','old_age_estimated_beneficiaries','Estimated scheme entries'),('Widow pension','widow_estimated_beneficiaries','Estimated scheme entries'),('Disability pension','disability_estimated_beneficiaries','Estimated scheme entries'),('Old age per 1,000','estimated_old_age_per_1000_population','Estimated entries / residents'),('Widow per 1,000','estimated_widow_per_1000_population','Estimated entries / residents'),('Crude literacy share','crude_literacy_share','Literate / total population'),('Dilapidated housing','dilapidated_pct','Percent of households'),('Open sanitation','open_defecation_pct','Percent of households'),('Households','total_households','Census household count')]
    for c1,c2,text in [(2,4,'Indicator'),(5,7,'=$C$3'),(8,10,'=$I$3'),(11,13,'How to read it')]:block(old,8,c1,c2,text,size=11,bold=True,color=WHITE,bg=NAVY,height=31)
    for r,(label,col,unit) in enumerate(metrics,9):
        bg=WHITE if r%2 else 'EAF0F6'
        block(old,r,2,4,label,size=10,bold=True,bg=bg,height=29)
        for c1,c2,selector in [(5,7,'C3'),(8,10,'I3')]:
            cell=block(old,r,c1,c2,f'=IFERROR(INDEX({rg(col)},MATCH(${selector[0]}$3,{rg("district_name")},0)),"Unavailable")',size=11,bg=bg,align='center')
            cell.number_format='0.0%' if col.endswith('_share') else '0.0"%"' if col.endswith('_pct') else '0.0' if 'score' in col or 'per_1000' in col else '#,##0'
        block(old,r,11,13,unit,size=9,color=MUTED,bg=bg)
    block(old,23,2,13,'Compare evidence, not just scores. Pension rates use total residents, not eligible elderly or widow populations.',size=10,color=MUTED,height=33)
    ch=BarChart();ch.title='Selected districts | priority score';ch.y_axis.title='Score / 100';ch.y_axis.scaling.min=0;ch.y_axis.scaling.max=100;ch.width=23;ch.height=8
    for c,selector,color in [(5,'C3',BLUE),(8,'I3',RED)]:
        ch.add_data(Reference(old,min_col=c,min_row=10,max_row=10));ch.series[-1].tx=SeriesLabel(strRef=StrRef(f="'District Comparison'!$"+selector[0]+"$3"));ch.series[-1].graphicalProperties.solidFill=color
    ch.dataLabels=DataLabelList();ch.dataLabels.showVal=True;ch.dataLabels.numFmt='0.0';ch.dataLabels.showSerName=False;ch.dataLabels.showCatName=False;ch.dataLabels.showLegendKey=False;ch.y_axis.numFmt='0';ch.y_axis.majorUnit=20;old.add_chart(ch,'B26')
    old.print_area='A1:N43';old.freeze_panes='B9'


def _guide(wb,profile,stamp,run_id):
    guide=wb['Dashboard Guide']
    for m in list(guide.merged_cells.ranges):guide.unmerge_cells(str(m))
    guide.delete_rows(1,guide.max_row);canvas(guide,53)
    block(guide,2,2,13,'How to use this dashboard',size=23,bold=True,color=WHITE,bg=NAVY,height=40,end=3)
    link(guide,5,2,6,'<  Back to overview','Executive Dashboard')
    notes=[('1. Start with the overview','Four headline figures describe the district records, High priority group, estimated scheme entries and district matching success. The High Priority list is sorted by the existing Gold rank.'),('2. Read the colors','Red = High, yellow = Medium, green = Low. The groups use the pipeline\'s existing deterministic ranking. Higher score means higher relative outreach priority, not proven scheme exclusion.'),('3. Understand the score','The Gold score combines low estimated old-age and widow rates with housing vulnerability and literacy proxies. Normalized inputs and weights are unchanged. No eligible elderly or widow denominator is available.'),('4. Explore the data','All district data opens the original mart. Use header filters to show a category or sort a value. The ML table retains its original fields and row colors. District Analysis contains the four additional charts.'),('5. Compare two districts','Open District Comparison and select names in the two yellow dropdown cells (C3 and I3). Excel updates the comparison table and score chart. Values labeled as housing percent are percentage points.'),('6. Interpret pension totals carefully','All pension counts are supplied district estimates. Summed scheme entries may include the same person more than once. Entries per 1,000 total residents are population-normalized rates, not eligible-person coverage.'),('7. Know the source limitations','Demographics are Census 2011. Pension reference year and the allocation method are unavailable. Housing total 100 is a percentage base; actual household counts come from Census Households. Unsupported measures stay unavailable.'),('8. Check district matching','Matching success = districts matched to all three sources / total districts. District Matching Report contains 72 source records and a 24-district status matrix. No unmatched record is hidden.'),('9. Refresh safely','Close generated Excel files, then rerun the pipeline. The workbook is a generated snapshot, not a live CSV connection. Editing raw values does not rebuild the ranked lists; regenerate after source changes.'),('10. Formulas and interactivity','Native Excel formulas, filters, charts, internal links and dropdowns are used. No VBA, macros, slicers or external APIs are required. Excel calculates on opening; a noncalculating viewer can show blank formula results.')]
    r=7
    for title,body in notes:
        block(guide,r,2,13,title,size=11,bold=True,color=NAVY,bg='E3EBF4',height=24)
        block(guide,r+1,2,13,body,size=10,color=MUTED,bg=WHITE,height=47);r+=4
    block(guide,48,2,13,'Data issues: '+('; '.join(profile['issues']) or 'None reported by the dashboard input checks.'),size=10,color=MUTED,height=30)
    block(guide,50,2,13,f'Generated {stamp} | Run {run_id}',size=9,color=MUTED,height=26)
    guide.print_area='A1:N52';guide.freeze_panes='B7'
