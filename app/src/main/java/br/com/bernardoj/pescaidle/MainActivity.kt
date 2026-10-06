package br.com.bernardoj.pescaidle

import android.app.*
import android.os.*
import android.content.*
import android.graphics.*
import android.graphics.drawable.ColorDrawable
import android.view.*
import android.widget.*
import org.json.JSONObject
import kotlin.math.*
import kotlin.random.Random

data class Loot(val nome:String,val cientifico:String,val valor:Double,val peso:Double,val tipo:String)

class MainActivity : Activity() {
    private lateinit var game: GameView
    override fun onCreate(b: Bundle?) { super.onCreate(b); game=GameView(this); setContentView(game) }
    override fun onPause() { game.save(); super.onPause() }
    override fun onResume() { super.onResume(); if (::game.isInitialized) game.resumeOffline() }
}

class GameView(private val ctx: Context) : View(ctx) {
    companion object { const val MAX=10; const val OFFLINE=4*3600_000L }
    private val p=Paint(Paint.ANTI_ALIAS_FLAG)
    private val mono=Typeface.MONOSPACE
    private val prefs=ctx.getSharedPreferences("pesca_idle",Context.MODE_PRIVATE)
    private var coins=0.0; private var rod=0; private var boat=0
    private var total=0; private var paused=false; private var wait=0.0; private var hook=0.0
    private var last=System.currentTimeMillis(); private var popup=""; private var popupUntil=0L
    private val inv=mutableMapOf<String,Int>()
    private val loot=listOf(
            Loot("Bota velha", "", 0, 8, "lixo"),
            Loot("Tubarão-lagarto", "Chlamydoselachus anguineus", 250, 0.18, "peixe"),
            Loot("Vaquita", "Phocoena sinus", 5000, 0.04, "peixe"),
            Loot("Celacanto-comorense", "Latimeria chalumnae", 2000, 0.08, "peixe"),
            Loot("Peixe-mão-vermelho", "Thymichthys politus", 5000, 0.025, "peixe"),
            Loot("Cavalinho-do-mar-pigmeu", "Hippocampus bargibanti", 120, 0.35, "peixe"),
            Loot("Lula-magnapinna", "Magnapinna spp.", 1800, 0.05, "peixe"),
            Loot("Tubarão-boca-grande", "Megachasma pelagios", 800, 0.10, "peixe"),
            Loot("Peixe-ogro", "Anoplogaster cornuta", 80, 0.5, "peixe"),
            Loot("Narval", "Monodon monoceros", 700, 0.12, "peixe"),
            Loot("Baleia-azul", "Balaenoptera musculus", 1000, 0.10, "peixe"),
            Loot("Tubarão-branco", "Carcharodon carcharias", 250, 0.20, "peixe"),
            Loot("Manta-gigante", "Mobula birostris", 180, 0.30, "peixe"),
            Loot("Peixe-lua", "Mola mola", 80, 0.60, "peixe"),
            Loot("Garoupa-verdadeira", "Epinephelus marginatus", 35, 1.0, "peixe"),
            Loot("Tartaruga-verde", "Chelonia mydas", 500, 0.08, "peixe"),
            Loot("Mero-preto", "Epinephelus itajara", 90, 0.40, "peixe"),
            Loot("Orca", "Orcinus orca", 650, 0.10, "peixe"),
            Loot("Peixe-papagaio-azul", "Scarus coeruleus", 8, 2.0, "peixe"),
            Loot("Polvo-comum", "Octopus vulgaris", 5, 2.5, "peixe"),
            Loot("Linguado-comum", "Solea solea", 4, 2.0, "peixe"),
            Loot("Golfinho-nariz-de-garrafa", "Tursiops truncatus", 150, 0.20, "peixe"),
            Loot("Barracuda-grande", "Sphyraena barracuda", 10, 1.7, "peixe"),
            Loot("Atum-azul", "Thunnus thynnus", 100, 0.20, "peixe"),
            Loot("Peixe-palhaço", "Amphiprion ocellaris", 2, 3.0, "peixe"),
            Loot("Lagosta-americana", "Homarus americanus", 3, 2.4, "peixe"),
            Loot("Água-viva-juba-de-leão", "Cyanea capillata", 1, 1.0, "peixe"),
            Loot("Lula-de-humboldt", "Dosidicus gigas", 2, 1.8, "peixe"),
            Loot("Salmão-rosa", "Oncorhynchus gorbuscha", 1.5, 3.0, "peixe"),
            Loot("Bacalhau-do-atlântico", "Gadus morhua", 2, 0.8, "peixe"),
            Loot("Cavala", "Scomber scombrus", 1, 4.5, "peixe"),
            Loot("Sardinha-do-pacífico", "Sardinops sagax", 0.5, 7, "peixe"),
            Loot("Anchoveta-peruana", "Engraulis ringens", 0.25, 12, "peixe"),
            Loot("Arenque-atlântico", "Clupea harengus", 0.25, 9, "peixe"),
            Loot("Polaca-do-alasca", "Gadus chalcogrammus", 0.3, 10, "peixe"),
            Loot("Camarão-cinza", "Crangon crangon", 0.2, 9, "peixe"),
            Loot("Mexilhão-azul", "Mytilus edulis", 0.1, 10, "peixe"),
            Loot("Caranguejo-falso", "Munida gregaria", 0.15, 7, "peixe"),
            Loot("Calano", "Calanus finmarchicus", 0.1, 10, "peixe"),
            Loot("Salpa-antártica", "Salpa thompsoni", 0.1, 8, "peixe"),
            Loot("Peixe-lanterna-glaciar", "Benthosema glaciale", 0.1, 9, "peixe"),
            Loot("Peixe-lanterna-de-müller", "Maurolicus muelleri", 0.1, 10, "peixe"),
            Loot("Krill-do-pacífico", "Euphausia pacifica", 0.1, 9, "peixe"),
            Loot("Krill-antártico", "Euphausia superba", 0.1, 12, "peixe"),
            Loot("Copépode-comum", "Acartia tonsa", 0.1, 12, "peixe"),
            Loot("Peixe-lanterna-comum", "Symbolophorus barnardi", 0.1, 7, "peixe"),
            Loot("Lambari", "Astyanax lacustris", 0.1, 8, "peixe"),
            Loot("Tilápia-do-nilo", "Oreochromis niloticus", 0.2, 4, "peixe"),
            Loot("Tambaqui", "Colossoma macropomum", 0.8, 1.5, "peixe"),
            Loot("Pacu", "Piaractus mesopotamicus", 0.5, 1.5, "peixe")
    )
    init { load(); resumeOffline(); wait=newWait(); last=System.currentTimeMillis(); setBackgroundColor(Color.rgb(20,30,72)) }
    private fun newWait()=(10.0+Random.nextDouble()*10.0)/(1+0.15*rod)
    private fun fmt(v:Double)=if(v>=1000) String.format("%,.0f",v).replace(",",".") else String.format("%.2f",v).trimEnd('0').trimEnd('.')
    private fun rarity(x:Loot)=when { x.peso>=8->"Comum"; x.peso>=3->"Incomum"; x.peso>=1->"Raro"; x.peso>=.1->"Muito raro"; else->"Lendário" }
    private fun fish():Loot {
        val weights=loot.map{it.peso*(if(it.valor>=25) 1+0.15*rod else 1)}
        var n=Random.nextDouble()*weights.sum()
        for(i in loot.indices){ n-=weights[i]; if(n<=0) return loot[i] }
        return loot.last()
    }
    private fun catchOne():String {
        val x=fish()
        if(x.tipo=="lixo") return "Bota velha... nada de útil"
        val gain=round(x.valor*(1+0.2*boat)*100)/100
        coins+=gain; total++; inv[x.nome]=(inv[x.nome]?:0)+1
        return "${x.nome}  +${fmt(gain)} moedas"
    }
    private fun process(dt:Double) {
        if(paused)return
        if(hook>0){ hook-=dt; if(hook<=0){ popup=catchOne(); popupUntil=System.currentTimeMillis()+3500; wait=newWait(); save() } }
        else { wait-=dt; if(wait<=0)hook=1.5 }
    }
    override fun onDraw(c:Canvas) {
        val now=System.currentTimeMillis(); val dt=min((now-last)/1000.0,.5); last=now; process(dt)
        drawScene(c); postInvalidateDelayed(66)
    }
    private fun text(c:Canvas,s:String,x:Float,y:Float,size:Float,color:Int=Color.WHITE){ p.typeface=mono;p.textSize=size;p.color=color;p.style=Paint.Style.FILL;c.drawText(s,x,y,p) }
    private fun box(c:Canvas,l:Float,t:Float,r:Float,b:Float,color:Int){p.color=color;p.style=Paint.Style.FILL;c.drawRect(l,t,r,b,p)}
    private fun drawScene(c:Canvas){
        val w=width.toFloat(); val h=height.toFloat()
        box(c,0f,0f,w,h,Color.rgb(18,27,67)); box(c,0f,0f,w,h*.40f,Color.rgb(75,106,178)); box(c,0f,h*.40f,w,h*.62f,Color.rgb(29,153,190)); box(c,0f,h*.62f,w,h,Color.rgb(18,94,130))
        p.color=Color.rgb(255,218,133);c.drawCircle(w*.82f,h*.20f,38f,p)
        for(i in 0..5){box(c,w*.08f+i*35,h*.12f+(i%2)*7,w*.08f+25+i*35,h*.14f+(i%2)*7,Color.rgb(214,231,239))}
        p.color=Color.rgb(46,67,105);val path=Path();path.moveTo(0f,h*.48f);path.lineTo(w*.20f,h*.25f);path.lineTo(w*.38f,h*.48f);path.lineTo(w*.55f,h*.28f);path.lineTo(w*.76f,h*.48f);path.lineTo(w,h*.30f);path.lineTo(w,h*.55f);path.lineTo(0f,h*.55f);path.close();c.drawPath(path,p)
        val bx=w*.08f; val by=h*.61f; val bw=w*.50f
        p.color=Color.rgb((177+rod*7).coerceAtMost(255),(91+rod*8).coerceAtMost(255),(53+rod*5).coerceAtMost(255));val hull=Path();hull.moveTo(bx,by);hull.lineTo(bx+bw,by);hull.lineTo(bx+bw*.86f,by+42);hull.lineTo(bx+bw*.12f,by+42);hull.close();c.drawPath(hull,p)
        box(c,bx+18,by-8,bx+bw-18,by+4,Color.rgb(245,204,91)); box(c,bx+28,by-105,bx+33,by-5,Color.rgb(72,48,43))
        p.color=Color.rgb(222,76,73);box(c,bx+35,by-70,bx+53,by-40,p.color);c.drawCircle(bx+44,by-82,11f,p)
        p.color=Color.rgb(50,35,44);p.strokeWidth=5f;c.drawLine(bx+48,by-55,w*.72f,h*.34f,p);p.strokeWidth=2f;p.color=Color.WHITE;c.drawLine(w*.72f,h*.34f,w*.72f,h*.59f,p);p.color=Color.rgb(255,91,103);c.drawCircle(w*.72f,h*.60f,9f,p)
        box(c,16f,18f,w-16f,94f,Color.argb(210,12,19,52)); text(c,"PESCA IDLE",28f,45f,22f,Color.rgb(255,218,133)); text(c,"Moedas: ${fmt(coins)}",28f,70f,16f); text(c,"Vara Nv ${rod}   Barco Nv ${boat}   Pescados ${total}",28f,90f,13f,Color.LTGRAY)
        if(popupUntil>System.currentTimeMillis()){box(c,20f,h*.48f,w-20f,h*.56f,Color.argb(225,20,25,50));text(c,popup,32f,h*.535f,15f,Color.rgb(255,218,133))}
        button(c,16f,h-88f,(w-40f)/3,h-24f,"LOJA");button(c,20f+(w-40f)/3,h-88f,20f+2*(w-40f)/3,h-24f,"ENCICLOPÉDIA");button(c,24f+2*(w-40f)/3,h-88f,w-16f,h-24f,if(paused)"▶" else "Ⅱ")
    }
    private fun button(c:Canvas,l:Float,t:Float,r:Float,b:Float,s:String){box(c,l,t,r,b,Color.rgb(38,49,100));p.color=Color.rgb(90,108,170);p.style=Paint.Style.STROKE;p.strokeWidth=2f;c.drawRect(l,t,r,b,p);p.style=Paint.Style.FILL;text(c,s,(l+r-measure(s,14f))/2,(t+b)/2+5,14f)}
    private fun measure(s:String,z:Float):Float{p.textSize=z;p.typeface=mono;return p.measureText(s)}
    override fun onTouchEvent(e:MotionEvent):Boolean{if(e.action!=MotionEvent.ACTION_UP)return true;if(e.y>height-105){val third=(width-40)/3;when{e.x<16+third->shop();e.x<20+2*third->encyclopedia();else->{paused=!paused;invalidate()}}};return true}
    private fun shop(){
        val d=Dialog(ctx);d.window?.setBackgroundDrawable(ColorDrawable(Color.rgb(20,27,60)));val l=LinearLayout(ctx);l.orientation=LinearLayout.VERTICAL;l.setPadding(32,28,32,20)
        val title=TextView(ctx);title.text="LOJA";title.textSize=24f;title.setTextColor(Color.rgb(255,218,133));l.addView(title)
        val info=TextView(ctx);info.setTextColor(Color.WHITE);l.addView(info)
        fun refresh(){info.text="Moedas: ${fmt(coins)}\n\nVara Nv ${rod} — peças ${parts("rod")}/${2+rod}\nBarco Nv ${boat} — peças ${parts("boat")}/${2+boat}"}
        refresh()
        val vr=Button(ctx);vr.text="Comprar peça da vara";vr.setOnClickListener{buy("rod");refresh();invalidate()};l.addView(vr)
        val br=Button(ctx);br.text="Comprar peça do barco";br.setOnClickListener{buy("boat");refresh();invalidate()};l.addView(br)
        val close=Button(ctx);close.text="Fechar";close.setOnClickListener{d.dismiss()};l.addView(close)
        d.setContentView(l);d.show();d.window?.setLayout(-1,-2)
    }
    private fun parts(kind:String):Int=prefs.getInt(if(kind=="rod")"rod_parts" else "boat_parts",0)
    private fun buy(kind:String){val level=if(kind=="rod")rod else boat;if(level>=MAX)return;val cost=30+20*level;if(coins<cost)return;coins-=cost;val key=if(kind=="rod")"rod_parts" else "boat_parts";var q=prefs.getInt(key,0)+1;if(q>=2+level){q-=2+level;if(kind=="rod")rod++ else boat++};prefs.edit().putInt(key,q).apply();save()}
    private fun encyclopedia(){
        val d=Dialog(ctx);d.window?.setBackgroundDrawable(ColorDrawable(Color.rgb(18,27,67)));val l=LinearLayout(ctx);l.orientation=LinearLayout.VERTICAL;l.setPadding(24,20,24,20)
        val title=TextView(ctx);title.text="ENCICLOPÉDIA";title.textSize=22f;title.setTextColor(Color.rgb(255,218,133));l.addView(title)
        val list=ListView(ctx);val found=loot.filter{it.tipo=="peixe"&&(inv[it.nome]?:0)>0}.sortedBy{it.nome};val names=found.map{"${it.nome} · ${inv[it.nome]}x"};list.adapter=ArrayAdapter(ctx,android.R.layout.simple_list_item_1,names);l.addView(list,LinearLayout.LayoutParams(-1,0,1f))
        val details=TextView(ctx);details.setTextColor(Color.WHITE);details.setPadding(8,12,8,12);l.addView(details)
        list.setOnItemClickListener{_,_,pos,_->val x=found[pos];val n=inv[x.nome]?:0;details.text="${x.nome}\n${x.cientifico}\n\nCapturas: ${n}\nValor: ${fmt(x.valor)} moedas\nRaridade: ${if(n>=5)rarity(x) else "Bloqueada — 5 capturas"}\nCuriosidade: ${if(n>=10)"Descoberta registrada no diário." else "Bloqueada — 10 capturas"}"}
        val close=Button(ctx);close.text="Fechar";close.setOnClickListener{d.dismiss()};l.addView(close);d.setContentView(l);d.show();d.window?.setLayout(-1,(ctx.resources.displayMetrics.heightPixels*.82).toInt())
    }
    fun save(){val j=JSONObject();j.put("coins",coins);j.put("rod",rod);j.put("boat",boat);j.put("total",total);j.put("last",System.currentTimeMillis());val invj=JSONObject();inv.forEach{(k,v)->invj.put(k,v)};j.put("inv",invj);j.put("rodParts",parts("rod"));j.put("boatParts",parts("boat"));prefs.edit().putString("state",j.toString()).apply()}
    private fun load(){val raw=prefs.getString("state",null)?:return;try{val j=JSONObject(raw);coins=j.optDouble("coins");rod=j.optInt("rod");boat=j.optInt("boat");total=j.optInt("total");val q=j.optJSONObject("inv");q?.keys()?.forEach{inv[it]=q.optInt(it)};prefs.edit().putInt("rod_parts",j.optInt("rodParts")).putInt("boat_parts",j.optInt("boatParts")).apply()}catch(_:Exception){}}
    fun resumeOffline(){val raw=prefs.getString("state",null)?:return;try{val lastSave=JSONObject(raw).optLong("last");if(lastSave==0L)return;val elapsed=min(System.currentTimeMillis()-lastSave,OFFLINE);if(elapsed<60_000)return;var t=0L;var count=0;while(t<elapsed){t+=((newWait()+1.5)*1000).toLong();if(t<=elapsed){catchOne();count++}};if(count>0){popup="Bem-vindo! ${count} pescarias offline.";popupUntil=System.currentTimeMillis()+4500;save()}}catch(_:Exception){}}
}
