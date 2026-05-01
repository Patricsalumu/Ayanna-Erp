<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class ComptaConfig extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'compta_config';
    protected $fillable = [
        'id', 'enterprise_id', 'pos_id',
        'compte_caisse_id', 'compte_banque_id', 'compte_stock_id', 'compte_variation_stock_id',
        'compte_client_id', 'compte_fournisseur_id', 'compte_fournisseur_debiteur_id',
        'compte_vente_id', 'compte_achat_id', 'compte_tva_id', 'compte_remise_id',
    ];

    public function pos()                        { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function enterprise()                 { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
    public function compteCaisse()               { return $this->belongsTo(ComptaComptes::class, 'compte_caisse_id'); }
    public function compteBanque()               { return $this->belongsTo(ComptaComptes::class, 'compte_banque_id'); }
    public function compteStock()                { return $this->belongsTo(ComptaComptes::class, 'compte_stock_id'); }
    public function compteClient()               { return $this->belongsTo(ComptaComptes::class, 'compte_client_id'); }
    public function compteFournisseur()          { return $this->belongsTo(ComptaComptes::class, 'compte_fournisseur_id'); }
    public function compteFournisseurDebiteur()  { return $this->belongsTo(ComptaComptes::class, 'compte_fournisseur_debiteur_id'); }
    public function compteVente()                { return $this->belongsTo(ComptaComptes::class, 'compte_vente_id'); }
    public function compteAchat()                { return $this->belongsTo(ComptaComptes::class, 'compte_achat_id'); }
    public function compteTva()                  { return $this->belongsTo(ComptaComptes::class, 'compte_tva_id'); }
    public function compteRemise()               { return $this->belongsTo(ComptaComptes::class, 'compte_remise_id'); }
}
