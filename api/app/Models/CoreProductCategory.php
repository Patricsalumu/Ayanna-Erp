<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class CoreProductCategory extends Model
{
    use HasUuids, SoftDeletes;
    protected $table = 'core_product_categories';
    protected $fillable = ['id', 'enterprise_id', 'name', 'description', 'parent_id', 'is_active'];
    protected $casts = ['is_active' => 'boolean'];

    public function enterprise() { return $this->belongsTo(Entreprise::class, 'enterprise_id'); }
    public function parent()     { return $this->belongsTo(CoreProductCategory::class, 'parent_id'); }
    public function children()   { return $this->hasMany(CoreProductCategory::class, 'parent_id'); }
    public function products()   { return $this->hasMany(CoreProduct::class, 'category_id'); }
}
