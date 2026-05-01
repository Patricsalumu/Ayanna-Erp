<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class AchatCommande extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'achat_commandes';
    protected $fillable = [
        'id', 'numero', 'fournisseur_id', 'entrepot_id', 'utilisateur_id',
        'date_commande', 'remise_global', 'montant_total', 'etat', 'statut_paiement',
    ];
    protected $casts = [
        'date_commande' => 'datetime',
        'montant_total' => 'decimal:2',
        'remise_global' => 'decimal:2',
    ];

    public function fournisseur()  { return $this->belongsTo(CoreFournisseur::class, 'fournisseur_id'); }
    public function entrepot()     { return $this->belongsTo(StockWarehouse::class, 'entrepot_id'); }
    public function utilisateur()  { return $this->belongsTo(User::class, 'utilisateur_id'); }
    public function lignes()       { return $this->hasMany(AchatCommandeLigne::class, 'bon_commande_id'); }
    public function depenses()     { return $this->hasMany(AchatDepense::class, 'bon_commande_id'); }
}
