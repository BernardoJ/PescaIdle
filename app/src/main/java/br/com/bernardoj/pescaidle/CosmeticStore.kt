package br.com.bernardoj.pescaidle

import android.app.Dialog
import android.content.Context
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.view.ViewGroup
import android.widget.*

data class Cosmetic(val id:String,val slot:String,val name:String,val price:Int)

object CosmeticStore {
    private val items = listOf(
        Cosmetic("chapeu_palha","Chapéus","Chapéu de palha",0),Cosmetic("chapeu_nenhum","Chapéus","Sem chapéu",0),Cosmetic("chapeu_bone","Chapéus","Boné azul",150),Cosmetic("chapeu_gorro","Chapéus","Gorro de lã",200),Cosmetic("chapeu_quepe","Chapéus","Quepe de capitão",500),Cosmetic("chapeu_pirata","Chapéus","Chapéu de pirata",800),Cosmetic("chapeu_cartola","Chapéus","Cartola",1200),Cosmetic("chapeu_coroa","Chapéus","Coroa dourada",5000),Cosmetic("chapeu_pikachu","Chapéus","Gorro do Pikachu",9999),Cosmetic("chapeu_ninja","Chapéus","Touca ninja",1800),Cosmetic("chapeu_samurai","Chapéus","Elmo de samurai",2600),Cosmetic("chapeu_cowboy","Chapéus","Chapéu de xerife",950),Cosmetic("chapeu_mago","Chapéus","Chapéu de arquimago",3200),Cosmetic("chapeu_astronauta","Chapéus","Capacete espacial",4100),Cosmetic("chapeu_folhas","Chapéus","Coroa de folhas",750),Cosmetic("chapeu_marinheiro","Chapéus","Boina de marinheiro",650),Cosmetic("chapeu_raposa","Chapéus","Capuz de raposa",2100),Cosmetic("chapeu_corais","Chapéus","Coroa de corais",2900),
        Cosmetic("roupa_vermelha","Roupas","Camisa vermelha",0),Cosmetic("roupa_azul","Roupas","Camisa azul",100),Cosmetic("roupa_verde","Roupas","Colete verde",250),Cosmetic("roupa_listrada","Roupas","Camisa listrada",400),Cosmetic("roupa_capa","Roupas","Capa de chuva",700),Cosmetic("roupa_capitao","Roupas","Casaco de capitão",1500),Cosmetic("roupa_gala","Roupas","Traje de gala",3000),Cosmetic("roupa_ninja","Roupas","Traje de ninja",2200),Cosmetic("roupa_astral","Roupas","Manto estelar",3500),Cosmetic("roupa_mergulhador","Roupas","Traje de mergulho",2800),Cosmetic("roupa_fenix","Roupas","Manto da fênix",5200),Cosmetic("roupa_cyber","Roupas","Jaqueta cyberpunk",4600),Cosmetic("roupa_mago","Roupas","Túnica de arquimago",3900),Cosmetic("roupa_marinheiro","Roupas","Uniforme de convés",850),Cosmetic("roupa_aurora","Roupas","Manto da aurora",4800),Cosmetic("roupa_abisso","Roupas","Armadura abissal",6800),
        Cosmetic("bandeira_nenhum","Bandeiras","Sem bandeira",0),Cosmetic("bandeira_vermelha","Bandeiras","Bandeirinha vermelha",100),Cosmetic("bandeira_brasil","Bandeiras","Bandeira do Brasil",300),Cosmetic("bandeira_arco","Bandeiras","Bandeira arco-íris",500),Cosmetic("bandeira_pirata","Bandeiras","Bandeira pirata",1000),Cosmetic("bandeira_dragao","Bandeiras","Bandeira do dragão",1300),Cosmetic("bandeira_nebulosa","Bandeiras","Bandeira nebulosa",1700),Cosmetic("bandeira_sol","Bandeiras","Bandeira do sol nascente",1400),Cosmetic("bandeira_kraken","Bandeiras","Bandeira do kraken",2100),Cosmetic("bandeira_galaxia","Bandeiras","Bandeira galáctica",2400),Cosmetic("bandeira_folhas","Bandeiras","Bandeira da floresta",950),Cosmetic("bandeira_sakura","Bandeiras","Bandeira de sakura",1150),Cosmetic("bandeira_tempestade","Bandeiras","Bandeira da tempestade",1850),Cosmetic("bandeira_compasso","Bandeiras","Bandeira do explorador",2750),
        Cosmetic("boia_vermelha","Boias","Boia vermelha",0),Cosmetic("boia_amarela","Boias","Boia amarela",100),Cosmetic("boia_listrada","Boias","Boia listrada",250),Cosmetic("boia_coracao","Boias","Boia coração",600),Cosmetic("boia_estrela","Boias","Boia estrela",1500),Cosmetic("boia_planeta","Boias","Boia planeta",2200),Cosmetic("boia_bolha","Boias","Boia de bolha",1200),Cosmetic("boia_donut","Boias","Boia de rosquinha",900),Cosmetic("boia_abacaxi","Boias","Boia de abacaxi",1300),Cosmetic("boia_kraken","Boias","Boia do kraken",2400),Cosmetic("boia_foguete","Boias","Boia foguete",1800),Cosmetic("boia_lotus","Boias","Boia de lótus",700),Cosmetic("boia_limao","Boias","Boia de limão",1050),Cosmetic("boia_perola","Boias","Boia pérola lunar",2800),
        Cosmetic("boneco_nenhum","Bonecos","Sem boneco",0),Cosmetic("boneco_pato","Bonecos","Patinho de borracha",300),Cosmetic("boneco_caranguejo","Bonecos","Caranguejo",700),Cosmetic("boneco_gato","Bonecos","Gatinho",1500),Cosmetic("boneco_pinguim","Bonecos","Pinguim",3000),Cosmetic("boneco_agumon","Bonecos","Agumon",9999),Cosmetic("boneco_robot","Bonecos","Robô explorador",6000),Cosmetic("boneco_slime","Bonecos","Mascote gelatinoso",4500),Cosmetic("boneco_raposa","Bonecos","Raposa mística",3800),Cosmetic("boneco_polvo","Bonecos","Polvo de pelúcia",2600),Cosmetic("boneco_capivara","Bonecos","Capivara aventureira",3300),Cosmetic("boneco_fantasma","Bonecos","Fantasma camarada",2200),Cosmetic("boneco_tartaruga","Bonecos","Tartaruguinha",1800),Cosmetic("boneco_axolote","Bonecos","Axolote sorridente",2700),Cosmetic("boneco_baleia","Bonecos","Baleia viajante",4100),
        Cosmetic("acessorio_nenhum","Acessórios","Sem acessório",0),Cosmetic("anel_verde_esmeralda","Acessórios","Anel Verde-Esmeralda",12000),Cosmetic("martelo_pesado","Acessórios","Martelo Pesado",15000),Cosmetic("teia_aracnidea","Acessórios","Lançador de Teia",10500),Cosmetic("orbe_dragon","Acessórios","Orbe do Dragão",14000),Cosmetic("broche_lunar","Acessórios","Broche Lunar",11500),Cosmetic("sabre_energia","Acessórios","Sabre de Energia",16000),Cosmetic("asas_fenix","Acessórios","Asas da Fênix",22000),Cosmetic("aura_cyber","Acessórios","Aura Cyberpunk",18500),Cosmetic("estrelas_orbitais","Acessórios","Constelação Orbital",20000),Cosmetic("chama_yokai","Acessórios","Chamas de Yokai",23500),Cosmetic("cajado_tempestade","Acessórios","Cajado da Tempestade",17000),Cosmetic("escudo_bolhas","Acessórios","Escudo de Bolhas",19000),Cosmetic("asas_boreais","Acessórios","Asas Boreais",25000)
    )

    fun show(
        ctx:Context,
        coins:()->Double,
        spend:(Double)->Boolean,
        isOwned:(String)->Boolean,
        equipped:(String)->String?,
        equip:(String,String)->Unit,
        save:()->Unit,
        format:(Double)->String
    ) {
        val dialog=Dialog(ctx)
        dialog.window?.setBackgroundDrawable(ColorDrawable(Color.rgb(18,27,67)))
        val root=LinearLayout(ctx);root.orientation=LinearLayout.VERTICAL;root.setPadding(18,16,18,12)
        val title=TextView(ctx);title.text="LOJA DE COSMÉTICOS";title.textSize=23f;title.setTextColor(Color.rgb(255,218,133));root.addView(title)
        val money=TextView(ctx);money.setTextColor(Color.WHITE);root.addView(money)
        val scroll=ScrollView(ctx);val list=LinearLayout(ctx);list.orientation=LinearLayout.VERTICAL

        fun rebuild(){
            money.text="Moedas: "+format(coins())
            list.removeAllViews()
            val groups=items.groupBy{it.slot}
            for((slot,group) in groups){
                val head=TextView(ctx);head.text=slot.uppercase();head.textSize=16f;head.setTextColor(Color.rgb(255,218,133));head.setPadding(0,14,0,5);list.addView(head)
                for(item in group.sortedWith(compareBy<Cosmetic>{it.price}.thenBy{it.name})){
                    val button=Button(ctx)
                    val owned=isOwned(item.id);val active=equipped(item.slot)==item.id
                    button.text=when{active->"✓ "+item.name+" — EQUIPADO";owned->item.name+" — Equipar";else->item.name+" — "+item.price+" moedas"}
                    button.setOnClickListener{
                        if(!isOwned(item.id)){
                            if(!spend(item.price)){Toast.makeText(ctx,"Moedas insuficientes",Toast.LENGTH_SHORT).show();return@setOnClickListener}
                        }
                        equip(item.slot,item.id);save();rebuild()
                    }
                    list.addView(button)
                }
            }
        }
        rebuild();scroll.addView(list);root.addView(scroll,LinearLayout.LayoutParams(-1,0,1f))
        val close=Button(ctx);close.text="Fechar";close.setOnClickListener{dialog.dismiss()};root.addView(close)
        dialog.setContentView(root);dialog.show();dialog.window?.setLayout(-1,(ctx.resources.displayMetrics.heightPixels*.90).toInt())
    }
}
