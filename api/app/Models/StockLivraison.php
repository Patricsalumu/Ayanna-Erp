<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class StockLivraison extends Model
{
    use HasUuids, SoftDeletes;

    protected $table = 'stock_livraisons';

    protected $fillable = [
        'id', 'numero', 'entreprise_id', 'entrepot_depart_id', 'entrepot_arrivee_id',
        'statut', 'valeur_totale', 'utilisateur_id', 'utilisateur_nom',
        'date_creation', 'date_livraison', 'date_reception', 'notes',
    ];

    protected $casts = [
        'valeur_totale'   => 'decimal:2',
        'date_creation'   => 'datetime',
        'date_livraison'  => 'datetime',
        'date_reception'  => 'datetime',
    ];

    public function entreprise()        { return $this->belongsTo(Entreprise::class, 'entreprise_id'); }
    public function entrepotDepart()    { return $this->belongsTo(StockWarehouse::class, 'entrepot_depart_id'); }
    public function entrepotArrivee()   { return $this->belongsTo(StockWarehouse::class, 'entrepot_arrivee_id'); }
    public function utilisateur()       { return $this->belongsTo(User::class, 'utilisateur_id'); }
    public function lignes()            { return $this->hasMany(StockLivraisonItem::class, 'livraison_id'); }
}
