<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class RestauPanier extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'restau_paniers';
    protected $fillable = [
        'id', 'pos_id', 'table_id', 'user_id', 'reference',
        'montant_total', 'montant_paye', 'remise', 'statut',
        'date_ouverture', 'date_fermeture', 'note', 'nombre_couverts',
    ];
    protected $casts = [
        'montant_total' => 'decimal:2', 'montant_paye' => 'decimal:2', 'remise' => 'decimal:2',
        'date_ouverture' => 'datetime', 'date_fermeture' => 'datetime',
    ];

    public function pos()             { return $this->belongsTo(POSPoint::class, 'pos_id'); }
    public function table()           { return $this->belongsTo(RestauTable::class, 'table_id'); }
    public function user()            { return $this->belongsTo(User::class, 'user_id'); }
    public function produits()        { return $this->hasMany(RestauProduitPanier::class, 'panier_id'); }
    public function paiements()       { return $this->hasMany(RestauPayment::class, 'panier_id'); }
    public function printedInvoices() { return $this->hasMany(RestauPrintedInvoice::class, 'panier_id'); }
}
